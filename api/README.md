- install requirements.txt
```bash
pip install -r requirements.txt
```
- create a database and a user
```bash
sudo mysql -u root
```
```sql
CREATE DATABASE <database_name>;
CREATE USER
    '<user_name>'@'localhost'
IDENTIFIED BY
    '<password>';
GRANT ALL PRIVILEGES ON <database_name>.* TO '<user_name>'@'localhost';
FLUSH PRIVILEGES;
```
- create a .env file in the root directory and add the following lines
```bash
MARIADB_USER='<user_name>'
MARIADB_PASSWORD='<password>'
MARIADB_DATABASE='<database_name>'
```