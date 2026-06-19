import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .supabase_client import get_client, get_service_client
from .corrections_data import SECTIONS

EDIT_WINDOW = getattr(settings, 'FORM_EDIT_WINDOW', 600)
NOTIFY = getattr(settings, 'FORM_NOTIFICATION_EMAILS', [])
TOTAL_CORRECTIONS = sum(len(s['items']) for s in SECTIONS)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_supabase_ts(ts_str):
    if not ts_str:
        return None
    ts = ts_str.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _lock_status(created_at_str):
    created_at = _parse_supabase_ts(created_at_str)
    if not created_at:
        return True, EDIT_WINDOW
    elapsed = (datetime.now(timezone.utc) - created_at).total_seconds()
    remaining = int(EDIT_WINDOW - elapsed)
    return remaining > 0, max(0, remaining)


def _send_notification(director_name, signature_date, submission_id):
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
        pass


# ── Corrections from Supabase (dynamic data layer) ───────────────────────────

def _fetch_all_corrections_supabase():
    """
    Returns (sections_list, True) from cug_correction_items, or (None, False).
    sections_list format matches SECTIONS from corrections_data.py so templates are compatible.
    """
    try:
        svc = get_service_client()
        result = (
            svc.table('cug_correction_items')
            .select('*')
            .order('section_order', desc=False)
            .order('num', desc=False)
            .execute()
        )
        if not result.data:
            return None, False

        sections_map = {}
        sections_order = []

        for row in result.data:
            sk = row['section_key']
            if sk not in sections_map:
                sections_map[sk] = {
                    'title': row.get('section_title', ''),
                    'section_key': sk,
                    'section_order': row.get('section_order', 0),
                    'items': [],
                }
                sections_order.append(sk)
            sections_map[sk]['items'].append({
                'id': row.get('correction_id', str(row['id'])),
                'db_id': row['id'],
                'num': row.get('num', 0),
                'module': row.get('module', ''),
                'correction': row.get('correction', ''),
                'action': row.get('action', ''),
                'is_done': row.get('is_done', False),
            })

        return [sections_map[sk] for sk in sections_order], True
    except Exception:
        return None, False


def _get_sections_and_done_set():
    """Returns (sections, done_set, from_supabase)."""
    sections, from_supabase = _fetch_all_corrections_supabase()
    if from_supabase:
        done_set = {
            item['id']
            for sec in sections
            for item in sec['items']
            if item.get('is_done')
        }
        return sections, done_set, True

    # Fall back: static sections + cug_corrections for is_done
    try:
        corrections_raw = get_client().table('cug_corrections').select('correction_id, is_done').execute()
        done_set = {r['correction_id'] for r in (corrections_raw.data or []) if r['is_done']}
    except Exception:
        done_set = set()
    return SECTIONS, done_set, False


# ── Main form view ────────────────────────────────────────────────────────────

def report_view(request):
    client = get_client()
    sections, done_set, _ = _get_sections_and_done_set()
    total = sum(len(s['items']) for s in sections)

    try:
        conf_result = (
            client.table('cug_director_confirmation')
            .select('id, director_name, signature_date, signature_data, other_comments, created_at')
            .order('created_at', desc=True)
            .limit(1)
            .execute()
        )
    except Exception:
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
        'sections': sections,
        'done_set': done_set,
        'confirmation': confirmation,
        'is_editable': is_editable,
        'has_submission': bool(confirmation),
        'total': total,
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

        svc = get_service_client()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Update cug_correction_items if item exists there
        try:
            svc.table('cug_correction_items').update(
                {'is_done': is_done, 'updated_at': now_iso}
            ).eq('correction_id', correction_id).execute()
        except Exception:
            pass

        # Also keep cug_corrections in sync (legacy)
        try:
            svc.table('cug_corrections').upsert(
                {'correction_id': correction_id, 'is_done': is_done},
                on_conflict='correction_id',
            ).execute()
        except Exception:
            pass

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
                return JsonResponse({
                    'error': 'name_exists',
                    'message': f'A confirmation from "{row["director_name"]}" has already been permanently recorded.',
                }, status=409)
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

    # Try to get total from supabase items, fall back to static
    _, from_supabase = _fetch_all_corrections_supabase()
    if from_supabase:
        try:
            svc = get_service_client()
            total_res = svc.table('cug_correction_items').select('id', count='exact').execute()
            total = total_res.count or TOTAL_CORRECTIONS
            done_count_res = svc.table('cug_correction_items').select('id', count='exact').eq('is_done', True).execute()
            done_count = done_count_res.count or done_count
        except Exception:
            total = TOTAL_CORRECTIONS
    else:
        total = TOTAL_CORRECTIONS

    submissions = []
    for sub in (subs_raw.data or []):
        is_editable, secs = _lock_status(sub.get('created_at'))
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
        'total': total,
        'pct': round(done_count / total * 100) if total else 0,
        'is_seeded': from_supabase,
    }
    return render(request, 'report/admin_dashboard.html', context)


# ── API: delete a submission ─────────────────────────────────────────────────

@require_http_methods(['POST'])
def delete_submission(request, submission_id):
    try:
        svc = get_service_client()
        check = svc.table('cug_director_confirmation').select('id').eq('id', submission_id).execute()
        if not check.data:
            return JsonResponse({'error': 'Record not found.'}, status=404)
        svc.table('cug_director_confirmation').delete().eq('id', submission_id).execute()
        verify = svc.table('cug_director_confirmation').select('id').eq('id', submission_id).execute()
        if verify.data:
            return JsonResponse({'error': 'Delete did not complete — check Supabase RLS policies.'}, status=500)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── Thanks page ──────────────────────────────────────────────────────────────

def thanks_view(request):
    return render(request, 'report/thanks.html')


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

    sections, done_set, _ = _get_sections_and_done_set()

    dt = _parse_supabase_ts(confirmation.get('created_at'))
    context = {
        'sections': sections,
        'done_set': done_set,
        'confirmation': confirmation,
        'submitted_at': dt.strftime('%d %B %Y at %H:%M UTC') if dt else '',
        'done_count': len(done_set),
        'total': sum(len(s['items']) for s in sections),
    }
    return render(request, 'report/print_report.html', context)


# ── Admin: Corrections Manager API ───────────────────────────────────────────

@require_http_methods(['GET'])
def admin_get_corrections(request):
    """Return all sections + items as JSON."""
    sections, seeded = _fetch_all_corrections_supabase()
    if not seeded:
        return JsonResponse({'sections': [], 'seeded': False})

    out = []
    for sec in sections:
        out.append({
            'section_key': sec['section_key'],
            'section_title': sec['title'],
            'section_order': sec['section_order'],
            'items': [
                {
                    'id': item['db_id'],
                    'correction_id': item['id'],
                    'num': item['num'],
                    'module': item['module'],
                    'correction': item['correction'],
                    'action': item['action'],
                    'is_done': item['is_done'],
                }
                for item in sec['items']
            ],
        })
    return JsonResponse({'sections': out, 'seeded': True})


@require_http_methods(['POST'])
def admin_seed_corrections(request):
    """Seed cug_correction_items from static corrections_data.SECTIONS."""
    try:
        svc = get_service_client()
        existing = svc.table('cug_correction_items').select('id').limit(1).execute()
        if existing.data:
            return JsonResponse({'success': True, 'message': 'Already seeded.', 'skipped': True})

        rows = []
        for sec_idx, section in enumerate(SECTIONS):
            sk = f's{sec_idx + 1}'
            for item in section['items']:
                rows.append({
                    'correction_id': item['id'],
                    'section_key': sk,
                    'section_title': section['title'],
                    'section_order': sec_idx + 1,
                    'num': item['num'],
                    'module': item['module'],
                    'correction': item['correction'],
                    'action': item['action'],
                    'is_done': False,
                })

        svc.table('cug_correction_items').insert(rows).execute()

        # Sync is_done from legacy cug_corrections
        try:
            done_raw = svc.table('cug_corrections').select('correction_id, is_done').execute()
            for rec in (done_raw.data or []):
                if rec['is_done']:
                    svc.table('cug_correction_items').update(
                        {'is_done': True}
                    ).eq('correction_id', rec['correction_id']).execute()
        except Exception:
            pass

        return JsonResponse({'success': True, 'message': f'Seeded {len(rows)} items.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def admin_add_correction_item(request):
    """Add a new correction item to a section."""
    try:
        data = json.loads(request.body)
        section_key   = data.get('section_key', '').strip()
        section_title = data.get('section_title', '').strip()
        section_order = int(data.get('section_order', 1))
        num           = int(data.get('num', 1))
        module        = data.get('module', '').strip()
        correction    = data.get('correction', '').strip()
        action        = data.get('action', '').strip()

        if not section_key:
            return JsonResponse({'error': 'section_key required'}, status=400)

        short_id = uuid.uuid4().hex[:8]
        correction_id = f'{section_key}_{short_id}'

        svc = get_service_client()
        result = svc.table('cug_correction_items').insert({
            'correction_id': correction_id,
            'section_key': section_key,
            'section_title': section_title,
            'section_order': section_order,
            'num': num,
            'module': module,
            'correction': correction,
            'action': action,
            'is_done': False,
        }).execute()

        new_row = result.data[0] if result.data else {}
        return JsonResponse({'success': True, 'item': {
            'id': new_row.get('id'),
            'correction_id': correction_id,
            'num': num,
            'module': module,
            'correction': correction,
            'action': action,
            'is_done': False,
        }})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def admin_update_correction_item(request, item_id):
    """Update fields of an existing correction item."""
    try:
        data = json.loads(request.body)
        svc = get_service_client()
        now_iso = datetime.now(timezone.utc).isoformat()

        update_data = {'updated_at': now_iso}
        for field in ('num', 'module', 'correction', 'action', 'is_done', 'section_title'):
            if field in data:
                if field == 'num':
                    update_data[field] = int(data[field])
                elif field == 'is_done':
                    update_data[field] = bool(data[field])
                else:
                    update_data[field] = str(data[field]).strip()

        svc.table('cug_correction_items').update(update_data).eq('id', item_id).execute()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def admin_delete_correction_item(request, item_id):
    """Delete a single correction item."""
    try:
        svc = get_service_client()
        svc.table('cug_correction_items').delete().eq('id', item_id).execute()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def admin_add_section(request):
    """Register a new section (returns metadata; items added separately)."""
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({'error': 'title required'}, status=400)

        svc = get_service_client()
        existing = (
            svc.table('cug_correction_items')
            .select('section_order, section_key')
            .order('section_order', desc=True)
            .limit(1)
            .execute()
        )
        max_order = existing.data[0]['section_order'] if existing.data else 0
        new_order = max_order + 1
        new_key = f's{new_order}_{uuid.uuid4().hex[:4]}'

        return JsonResponse({
            'success': True,
            'section': {
                'section_key': new_key,
                'section_title': title,
                'section_order': new_order,
                'items': [],
            },
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def admin_update_section_title(request, section_key):
    """Rename a section (updates all rows that share this section_key)."""
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({'error': 'title required'}, status=400)

        svc = get_service_client()
        now_iso = datetime.now(timezone.utc).isoformat()
        svc.table('cug_correction_items').update(
            {'section_title': title, 'updated_at': now_iso}
        ).eq('section_key', section_key).execute()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def admin_delete_section(request, section_key):
    """Delete all items in a section."""
    try:
        svc = get_service_client()
        svc.table('cug_correction_items').delete().eq('section_key', section_key).execute()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
