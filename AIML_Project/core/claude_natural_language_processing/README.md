1. Install Dependencies
bashpip install flask cx_Oracle
```

### 2. Create Project Structure
```
your_project/
├── app.py              (Copy from artifact 1)
└── templates/
    └── index.html      (Copy from artifact 2)
3. Update Database Configuration
Edit app.py and update lines 9-19 with your database credentials:
pythonPROD_DB_CONFIG = {
    'user': 'your_prod_username',
    'password': 'your_prod_password',
    'dsn': 'your_host:1521/PRODDB'
}

PTE_DB_CONFIG = {
    'user': 'your_pte_username',
    'password': 'your_pte_password',
    'dsn': 'your_host:1521/PTEDB'
}
4. Run the Application
bashpython app.py
5. Access the Interface
Open your browser and go to: http://localhost:5000
