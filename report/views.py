import json
from datetime import datetime, timezone, timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .supabase_client import get_client, get_service_client
from .corrections_data import SECTIONS

EDIT_WINDOW = getattr(settings, 'FORM_EDIT_WINDOW', 600)  # seconds
NOTIFY = getattr(settings, 'FORM_NOTIFICATION_EMAILS', [])
TOTAL_CORRECTIONS = sum(len(s['items']) for s in SECTIONS)  # 25


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_supabase_ts(ts_str):
    """Parse a Supabase ISO-8601 timestamp → aware datetime."""
    if not ts_str:
        return None
    ts = ts_str.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _lock_status(created_at_str):
    """Return (is_editable: bool, seconds_remaining: int)."""
    created_at = _parse_supabase_ts(created_at_str)
    if not created_at:
        return True, EDIT_WINDOW
    elapsed = (datetime.now(timezone.utc) - created_at).total_seconds()
    remaining = int(EDIT_WINDOW - elapsed)
    return remaining > 0, max(0, remaining)


def _send_notification(director_name, signature_date, submission_id):
    """Fire-and-forget email to all notification addresses."""
    if not NOTIFY:
        return
    subject = 'CUG Archival System — Corrections Report Submitted'
    host = os.getenv('SITE_URL', 'http://udtsform.sslip.io')
    text = (
        f"The ICT Director Confirmation Form has been submitted.\n\n"
        f"Director: {director_name or '(not entered)'}\n"
        f"Date:     {signature_date or '(not entered)'}\n\n"
        f"View the admin dashboard: {host}/admin/\n"
        f"Print / export report:    {host}/admin/print/{submission_id}/\n"
    )
    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#111;max-width:600px;margin:auto">
    <div style="background:#1a1a1a;padding:20px 30px;border-radius:6px 6px 0 0">
      <h2 style="color:#fff;margin:0">CUG Archival System</h2>
      <p style="color:#aaa;margin:4px 0 0">Archival Corrections Report — Form Submitted</p>
    </div>
    <div style="background:#f9f9f9;padding:24px 30px;border:1px solid #ddd;border-top:none;border-radius:0 0 6px 6px">
      <p>The ICT Director Confirmation Form has been filled and saved.</p>
      <table style="border-collapse:collapse;width:100%;margin:16px 0">
        <tr><td style="padding:6px 0;font-weight:bold;width:120px">Director</td>
            <td style="padding:6px 0">{director_name or '<em>not entered</em>'}</td></tr>
        <tr><td style="padding:6px 0;font-weight:bold">Date</td>
            <td style="padding:6px 0">{signature_date or '<em>not entered</em>'}</td></tr>
      </table>
      <p>
        <a href="{host}/admin/"
           style="background:#1a1a1a;color:#fff;padding:10px 20px;text-decoration:none;border-radius:4px;display:inline-block;margin-right:10px">
           View Dashboard
        </a>
        <a href="{host}/admin/print/{submission_id}/"
           style="background:#555;color:#fff;padding:10px 20px;text-decoration:none;border-radius:4px;display:inline-block">
           Print / Export Report
        </a>
      </p>
    </div>
    </body></html>
    """
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=NOTIFY,
        )
        msg.attach_alternative(html, 'text/html')
        msg.send(fail_silently=True)
    except Exception:
        pass  # never break the user's save over an email failure


# ── Main form view ────────────────────────────────────────────────────────────

def report_view(request):
    client = get_client()

    result = client.table('cug_corrections').select('correction_id, is_done').execute()
    done_set = {r['correction_id'] for r in (result.data or []) if r['is_done']}

    try:
        conf_result = (
            client.table('cug_director_confirmation')
            .select('id, director_name, signature_date, signature_data, other_comments, created_at')
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
    except Exception:
        # columns may not exist yet — run supabase_migrations.sql
        conf_result = (
            client.table('cug_director_confirmation')
            .select('id, director_name, signature_date, created_at')
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
    confirmation = conf_result.data[0] if conf_result.data else None
    if confirmation:
        confirmation.setdefault('signature_data', None)
        confirmation.setdefault('other_comments', None)

    is_editable = True
    seconds_remaining = EDIT_WINDOW
    if confirmation:
        is_editable, seconds_remaining = _lock_status(confirmation.get('created_at'))

    context = {
        'sections': SECTIONS,
        'done_set': done_set,
        'confirmation': confirmation,
        'is_editable': is_editable,
        'has_submission': bool(confirmation),
    }
    return render(request, 'report/index.html', context)


# ── API: toggle a correction checkbox ────────────────────────────────────────

@require_http_methods(['POST'])
def update_correction(request):
    try:
        data = json.loads(request.body)
        correction_id = data.get('correction_id', '').strip()
        is_done = bool(data.get('is_done', False))
        if not correction_id:
            return JsonResponse({'error': 'correction_id required'}, status=400)

        get_service_client().table('cug_corrections').upsert(
            {'correction_id': correction_id, 'is_done': is_done},
            on_conflict='correction_id',
        ).execute()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── API: save confirmation (name + signature + date) ─────────────────────────

@require_http_methods(['POST'])
def save_confirmation(request):
    try:
        data     = json.loads(request.body)
        name     = data.get('director_name', '').strip()
        date     = data.get('signature_date', '').strip() or None
        sig      = data.get('signature_data', '').strip() or None
        comments = data.get('other_comments', '').strip() or None
        svc      = get_service_client()

        if not name:
            return JsonResponse({'error': 'name_required', 'message': 'Director name is required.'}, status=400)

        # Find any existing submission matching this director name (case-insensitive)
        name_match = (
            svc.table('cug_director_confirmation')
            .select('id, created_at, director_name')
            .ilike('director_name', name)
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
        row = name_match.data[0] if name_match.data else None

        if row:
            is_editable, _ = _lock_status(row.get('created_at'))
            if not is_editable:
                # Name already has a permanently locked submission — block re-submission
                return JsonResponse({
                    'error': 'name_exists',
                    'message': f'A confirmation from "{row["director_name"]}" has already been permanently recorded.',
                }, status=409)
            # Same name within edit window → allow update
            try:
                svc.table('cug_director_confirmation').update(
                    {'director_name': name, 'signature_date': date, 'signature_data': sig, 'other_comments': comments}
                ).eq('id', row['id']).execute()
            except Exception:
                svc.table('cug_director_confirmation').update(
                    {'director_name': name, 'signature_date': date}
                ).eq('id', row['id']).execute()
            return JsonResponse({'success': True, 'submission_id': row['id'], 'updated': True})
        else:
            # New name — insert first submission
            try:
                ins = svc.table('cug_director_confirmation').insert(
                    {'director_name': name, 'signature_date': date, 'signature_data': sig, 'other_comments': comments}
                ).execute()
            except Exception:
                ins = svc.table('cug_director_confirmation').insert(
                    {'director_name': name, 'signature_date': date}
                ).execute()
            sub_id = ins.data[0]['id'] if ins.data else None
            _send_notification(name, date, sub_id)
            return JsonResponse({'success': True, 'submission_id': sub_id, 'updated': False})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── Admin dashboard ───────────────────────────────────────────────────────────

def admin_dashboard(request):
    client = get_client()

    try:
        subs_raw = (
            client.table('cug_director_confirmation')
            .select('id, director_name, signature_date, signature_data, other_comments, created_at')
            .order('created_at', desc=True)
            .execute()
        )
    except Exception:
        subs_raw = (
            client.table('cug_director_confirmation')
            .select('id, director_name, signature_date, created_at')
            .order('created_at', desc=True)
            .execute()
        )
    for row in (subs_raw.data or []):
        row.setdefault('signature_data', None)
        row.setdefault('other_comments', None)

    corrections_raw = (
        client.table('cug_corrections')
        .select('correction_id, is_done')
        .execute()
    )
    done_set   = {r['correction_id'] for r in (corrections_raw.data or []) if r['is_done']}
    done_count = len(done_set)

    submissions = []
    for sub in (subs_raw.data or []):
        is_editable, secs = _lock_status(sub.get('created_at'))
        # Parse created_at for display
        dt = _parse_supabase_ts(sub.get('created_at'))
        submissions.append({
            **sub,
            'is_editable': is_editable,
            'seconds_remaining': secs,
            'created_at_display': dt.strftime('%d %b %Y, %H:%M') if dt else '—',
        })

    context = {
        'submissions': submissions,
        'done_count': done_count,
        'total': TOTAL_CORRECTIONS,
        'pct': round(done_count / TOTAL_CORRECTIONS * 100) if TOTAL_CORRECTIONS else 0,
    }
    return render(request, 'report/admin_dashboard.html', context)


# ── API: delete a submission ─────────────────────────────────────────────────

@require_http_methods(['POST'])
def delete_submission(request, submission_id):
    try:
        svc = get_service_client()
        # Verify record exists before deleting
        check = svc.table('cug_director_confirmation').select('id').eq('id', submission_id).execute()
        if not check.data:
            return JsonResponse({'error': 'Record not found.'}, status=404)
        # Delete from Supabase (service key bypasses RLS)
        svc.table('cug_director_confirmation').delete().eq('id', submission_id).execute()
        # Confirm it is gone
        verify = svc.table('cug_director_confirmation').select('id').eq('id', submission_id).execute()
        if verify.data:
            return JsonResponse({'error': 'Delete did not complete — check Supabase RLS policies.'}, status=500)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── Print / PDF view ─────────────────────────────────────────────────────────

def print_report(request, submission_id):
    client = get_client()

    try:
        subs = (
            client.table('cug_director_confirmation')
            .select('id, director_name, signature_date, signature_data, other_comments, created_at')
            .eq('id', submission_id)
            .execute()
        )
    except Exception:
        subs = (
            client.table('cug_director_confirmation')
            .select('id, director_name, signature_date, created_at')
            .eq('id', submission_id)
            .execute()
        )
    if not subs.data:
        raise Http404('Submission not found')
    confirmation = subs.data[0]
    confirmation.setdefault('signature_data', None)
    confirmation.setdefault('other_comments', None)

    corrections_raw = (
        client.table('cug_corrections')
        .select('correction_id, is_done')
        .execute()
    )
    done_set = {r['correction_id'] for r in (corrections_raw.data or []) if r['is_done']}

    dt = _parse_supabase_ts(confirmation.get('created_at'))
    context = {
        'sections': SECTIONS,
        'done_set': done_set,
        'confirmation': confirmation,
        'submitted_at': dt.strftime('%d %B %Y at %H:%M UTC') if dt else '',
        'done_count': len(done_set),
        'total': TOTAL_CORRECTIONS,
    }
    return render(request, 'report/print_report.html', context)
