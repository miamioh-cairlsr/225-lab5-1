from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# Database file path
DATABASE = '/nfs/demo.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row  # This enables name-based access to columns
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            );
        ''')
        db.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''  # Message indicating the result of the operation
    if request.method == 'POST':
        # Check if it's a delete action
        if request.form.get('action') == 'delete':
            contact_id = request.form.get('contact_id')
            db = get_db()
            db.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
            db.commit()
            message = 'Contact deleted successfully.'
        else:
            name = request.form.get('name')
            phone = request.form.get('phone')
            if name and phone:
                db = get_db()
                db.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (name, phone))
                db.commit()
                message = 'Contact added successfully.'
            else:
                message = 'Missing name or phone number.'

    # Always display the contacts table
    db = get_db()
    contacts = db.execute('SELECT * FROM contacts').fetchall()

    # Display the HTML form along with the contacts table
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Contacts</title>
        </head>
        <body>
            <h2>Add Contacts</h2>
            <form method="POST" action="/">
                <label for="name">Name:</label><br>
                <input type="text" id="name" name="name" required><br>
                <label for="phone">Phone Number:</label><br>
                <input type="text" id="phone" name="phone" required><br><br>
                <input type="submit" value="Submit">
            </form>
            <p>{{ message }}</p>
            {% if contacts %}
                <table border="1">
                    <tr>
                        <th>Name</th>
                        <th>Phone Number</th>
                        <th>Actions</th>
                    </tr>
                    {% for contact in contacts %}
                        <tr>
                            <td>{{ contact['name'] }}</td>
                            <td>{{ contact['phone'] }}</td>
                            <td>
                                <form method="POST" action="/" style="display:inline;">
                                    <input type="hidden" name="contact_id" value="{{ contact['id'] }}">
                                    <input type="hidden" name="action" value="delete">
                                    <input type="submit" value="Delete">
                                </form>
                                <form method="GET" action="{{ url_for('update_contact', contact_id=contact['id']) }}" style="display:inline;">
                                    <input type="submit" value="Update">
                                </form>
                            </td>
                        </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>No contacts found.</p>
            {% endif %}
        </body>
        </html>
    ''', message=message, contacts=contacts)

@app.route('/update/<int:contact_id>', methods=['GET', 'POST'])
def update_contact(contact_id):
    db = get_db()
    if request.method == 'POST':
        # Process update form submission
        name = request.form.get('name')
        phone = request.form.get('phone')
        if name and phone:
            db.execute('UPDATE contacts SET name = ?, phone = ? WHERE id = ?', (name, phone, contact_id))
            db.commit()
            return redirect(url_for('index'))
        else:
            message = "Please provide both name and phone."
    else:
        # Show the update form pre-filled with current contact info
        contact = db.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,)).fetchone()
        if contact is None:
            return "Contact not found", 404
        message = ''

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>Update Contact</title></head>
        <body>
            <h2>Update Contact</h2>
            <form method="POST">
                <label for="name">Name:</label><br>
                <input type="text" id="name" name="name" value="{{ contact['name'] }}" required><br>
                <label for="phone">Phone Number:</label><br>
                <input type="text" id="phone" name="phone" value="{{ contact['phone'] }}" required><br><br>
                <input type="submit" value="Update">
            </form>
            <p>{{ message }}</p>
            <p><a href="{{ url_for('index') }}">Back to contacts</a></p>
        </body>
        </html>
    ''', contact=contact, message=message)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    init_db()  # Initialize the database and table
    app.run(debug=True, host='0.0.0.0', port=port)
