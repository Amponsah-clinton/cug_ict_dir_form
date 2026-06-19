"""
Static correction items. Only the is_done status lives in Supabase.
Each item's 'id' is the key used for Supabase upsert/lookup.
"""

SECTIONS = [
    {
        'title': '1.0 CORRECTIONS GIVEN ON SUNDAY, 17TH MAY, 2026',
        'items': [
            {
                'id': 's1_01', 'num': 1, 'module': 'File Deposit',
                'correction': "The depositor's name and email should be non-responsive/non-editable.",
                'action': "Make the depositor's name and email read-only so users cannot edit or change them during file deposit.",
            },
            {
                'id': 's1_02', 'num': 2, 'module': 'File Deposit',
                'correction': "The depositor's unit/department should be static with no editable option.",
                'action': "Auto-display the depositor's unit or department as read-only.",
            },
            {
                'id': 's1_03', 'num': 3, 'module': 'File Deposit',
                'correction': "If a depositor belongs to two departments, all departments should show.",
                'action': "Configure the system to display all assigned departments/units linked to the depositor.",
            },
            {
                'id': 's1_04', 'num': 4, 'module': 'File Deposit',
                'correction': "Uploaded files should not be downloadable.",
                'action': "Disable download access for deposited files where required.",
            },
            {
                'id': 's1_05', 'num': 5, 'module': 'File Deposit',
                'correction': "Uploaded files should be previewable.",
                'action': "Add file preview functionality for deposited files.",
            },
            {
                'id': 's1_06', 'num': 6, 'module': 'File Deposit',
                'correction': "After successful upload, the file name should be editable.",
                'action': "Allow authorized users to edit only the file name after upload, without changing the file content.",
            },
            {
                'id': 's1_07', 'num': 7, 'module': 'File Deposit',
                'correction': "There should be a folder where specific files will be saved.",
                'action': "Create or assign specific folders for categorised storage of selected files.",
            },
            {
                'id': 's1_08', 'num': 8, 'module': 'Archive System',
                'correction': "When a folder is created, users should be added to access the folder.",
                'action': "Add folder-level access control to allow selected users to access specific folders.",
            },
            {
                'id': 's1_09', 'num': 9, 'module': 'Exams File Deposit',
                'correction': "The depositor's name and email should be non-responsive/non-editable.",
                'action': "Make the depositor's name and email read-only during exams file deposit.",
            },
            {
                'id': 's1_10', 'num': 10, 'module': 'Exams File Deposit',
                'correction': "The depositor's unit should be static with no selectable/editable option.",
                'action': "Auto-display the depositor's unit as read-only during exams file deposit.",
            },
            {
                'id': 's1_11', 'num': 11, 'module': 'Exams File Deposit',
                'correction': "A future date, 20th May, was selected successfully; this should not be allowed.",
                'action': "Restrict date selection to today's date or yesterday's date only. Tomorrow or any future date should be blocked.",
            },
            {
                'id': 's1_12', 'num': 12, 'module': 'Folder Creation',
                'correction': "After creating a folder, the folder does not appear in the folder list.",
                'action': "Fix the folder creation process so newly created folders appear immediately in the folder section.",
            },
            {
                'id': 's1_13', 'num': 13, 'module': 'Folder Creation',
                'correction': 'File names should follow a clear naming format such as “Information Technology – Date Deposited.”',
                'action': "Apply a standard file-naming format using department/unit name and date of deposit for easy identification.",
            },
        ],
    },
    {
        'title': '2.0 CORRECTIONS GIVEN ON THURSDAY, 11TH JUNE, 2026',
        'items': [
            {
                'id': 's2_01', 'num': 1, 'module': 'Login / System Alert',
                'correction': "Remove the long Meta IronDom alert at login.",
                'action': "Remove or shorten the login alert message to improve user experience.",
            },
            {
                'id': 's2_02', 'num': 2, 'module': 'Compose Memo',
                'correction': "Add memo type selection after letterhead selection and before memo subject.",
                'action': "Add radio buttons for memo type: Promotion Memo, Procurement Memo, Leave Memo, and Other.",
            },
            {
                'id': 's2_03', 'num': 3, 'module': 'Memo Notification / Bell Alert',
                'correction': "When a user receives a memo alert through the bell notification, the privileges to act on the memo should also be available in the memo portal.",
                'action': "Ensure that users can open, view, comment, act, or respond to memo notifications according to their assigned privileges.",
            },
            {
                'id': 's2_04', 'num': 4, 'module': 'Compose Memo',
                'correction': 'Add a “Through” button/field to the memo routing structure.',
                'action': 'Add a “Through” field between “To” and “Cc” to support formal memo routing.',
            },
            {
                'id': 's2_05', 'num': 5, 'module': 'Compose Memo',
                'correction': "Memo format should support: From, To, Through, Cc, and Subject.",
                'action': "Configure memo layout to follow the structure: From: Ag. ICT Director; To: Vice-Chancellor; Through: Pro Vice-Chancellor; Cc: Dean of CEMS, RSS; Subject: Purchase of Clocking Machine.",
            },
            {
                'id': 's2_06', 'num': 6, 'module': 'Compose Memo / Cc Function',
                'correction': "Persons copied in Cc should have an option to comment on the memo.",
                'action': "Enable comment privileges for users copied in the Cc field.",
            },
            {
                'id': 's2_07', 'num': 7, 'module': 'Export / Print / PDF Preview',
                'correction': "Export and print should include preview of uploaded PDF together with memo content.",
                'action': "Ensure exported or printed memo documents include both the memo content and attached PDF preview where applicable.",
            },
            {
                'id': 's2_08', 'num': 8, 'module': 'Dashboard',
                'correction': "Close to the bell notification icon, there should be a button indicating whether the page is User or Admin.",
                'action': "Add a clear User/Admin mode indicator on the dashboard near the notification bell.",
            },
            {
                'id': 's2_09', 'num': 9, 'module': 'User Profile / Normal Users',
                'correction': "Normal users should not be able to edit their position or other official profile sections.",
                'action': "Make official user profile details such as position, department, and role static/read-only for normal users.",
            },
            {
                'id': 's2_10', 'num': 10, 'module': 'Documentation Menu',
                'correction': '“System Documentation” should be changed to “University Policies.”',
                'action': 'Rename the menu item from “System Documentation” to “University Policies.”',
            },
            {
                'id': 's2_11', 'num': 11, 'module': 'User Manual',
                'correction': 'Add another button called “User Manual.”',
                'action': 'Add a separate “User Manual” button/menu item for system usage guidance.',
            },
            {
                'id': 's2_12', 'num': 12, 'module': 'CSV File Preview',
                'correction': "CSV files were uploaded but could not be previewed.",
                'action': "Add preview support for uploaded CSV files.",
            },
        ],
    },
]
