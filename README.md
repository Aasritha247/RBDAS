# RBDAS
📄 RBDAS - Role-Based Document Accessibility System
The Role-Based Document Accessibility System (RBDAS) is a secure, role-driven document management web application that controls user access to documents based on assigned roles such as Admin, Editor, and Viewer.

🔐 Key Features:
User Authentication: Login and registration with session management.

Role Selection: Users select a role (Admin, Editor, Viewer) which dictates access rights.

Document Upload & Storage: Upload and store documents securely.

Role-Based Access Control:

Admins can upload, delete, edit, and share documents.

Editors can view and modify shared documents.

Viewers can only view documents shared with them.

Sharing with Access Rights: Documents can be shared with specific users via email with view/edit permissions.

Version Control: Modified documents retain edit history or latest version for Editors.

Modern UI: Clean, responsive frontend using HTML, CSS (Bootstrap), and JavaScript.

Database Integration: Uses SQLite3 / Oracle SQL for persistent user and document data.

⚙️ Tech Stack:
Frontend: HTML, CSS (Bootstrap), JavaScript

Backend: Python Flask

Database: SQLite3 / Oracle SQL (configurable)

Session Management: Flask Sessions

Authentication: Password hashing with secure login

🧪 How It Works:
User selects role and logs in.

Based on role:

Can upload, edit, delete, or view documents.

Shared documents display sender’s email and access rights.

Editor modifications are tracked and stored separately.
