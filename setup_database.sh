#!/bin/bash
export PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
set -x
set -euo pipefail
# Variables
DB_NAME="persona_db"
DB_USER="persona_user"
DB_PASSWORD="secure_password"
POSTGRES_PASSWORD="postgres_password"
PG_HBA_CONF="/var/lib/pgsql/15/data/pg_hba.conf"
PG_DATA_DIR="/var/lib/pgsql/15/data"

# Function to install PostgreSQL on RHEL
install_postgresql_rhel() {
    sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-$(rpm -E %{rhel})-x86_64/pgdg-redhat-repo-latest.noarch.rpm
    sudo yum install -y postgresql15-server postgresql15
}

# Function to install PostgreSQL on Ubuntu
install_postgresql_ubuntu() {
    sudo apt-get update
    sudo apt-get install -y postgresql-15
}

# Function to install pgvector extension
install_pgvector() {
    echo "Installing pgvector extension..."
    if [ -f /etc/redhat-release ]; then
        sudo yum install -y pgvector_15
    elif [ -f /etc/lsb-release ]; then
        sudo apt-get install -y postgresql-15-pgvector
    fi
}

# Function to cleanup PostgreSQL installation
cleanup_postgresql() {
    echo "Cleaning up PostgreSQL installation..."
    if systemctl is-active --quiet postgresql-15; then
        sudo systemctl stop postgresql-15
        sudo systemctl disable postgresql-15
    fi
    sudo yum remove -y postgresql15-server postgresql15 || sudo apt-get remove -y postgresql-15
    sudo rm -rf /var/lib/pgsql/15/data
    echo "PostgreSQL installation cleaned up."
}

# Function to cleanup database and user
cleanup_database() {
    echo "Cleaning up database and user..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
    sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;"
    echo "Database and user cleaned up."
}

# Detect OS and install PostgreSQL
detect_os_and_install() {
    if [ -f /etc/redhat-release ]; then
        echo "Detected RHEL-based system"
        install_postgresql_rhel
    elif [ -f /etc/lsb-release ]; then
        echo "Detected Ubuntu-based system"
        install_postgresql_ubuntu
    else
        echo "Unsupported OS"
        exit 1
    fi
}

# Check if the data directory is already initialized
check_data_directory() {
    if [ ! "$(ls -A $PG_DATA_DIR)" ]; then
        echo "Initializing PostgreSQL database..."
        sudo /usr/pgsql-15/bin/postgresql-15-setup initdb
    else
        echo "PostgreSQL database already initialized. Skipping initdb."
    fi
}

# Start PostgreSQL service
start_postgresql_service() {
    sudo systemctl enable postgresql-15
    sudo systemctl start postgresql-15
}

# Get the pg_hba.conf location dynamically
get_pg_hba_conf_location() {
    PG_HBA_CONF=$(sudo -u postgres psql -t -P format=unaligned -c "SHOW hba_file")
    if [ -z "$PG_HBA_CONF" ]; then
        echo "Failed to fetch pg_hba.conf location. Exiting..."
        exit 1
    fi
}

# Update pg_hba.conf to use md5 authentication
update_pg_hba_conf() {
    echo "Updating $PG_HBA_CONF to use md5 authentication..."
    sudo sed -i 's#host\s\+all\s\+all\s\+127\.0\.0\.1/32\s\+ident#host all all 127.0.0.1/32 md5#' "$PG_HBA_CONF"
    sudo sed -i 's#host\s\+all\s\+all\s\+::1/128\s\+ident#host all all ::1/128 md5#' "$PG_HBA_CONF"
    echo "pg_hba.conf updated successfully."
}

# Reload PostgreSQL configuration
reload_postgresql_configuration() {
    sudo systemctl restart postgresql-15
}

# Set password for postgres user
set_postgres_password() {
    echo "Setting postgres user password..."
    sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$POSTGRES_PASSWORD';"
}

# Test postgres connection
test_postgres_connection() {
    echo "Testing postgres connection..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h 127.0.0.1 -c "\q" || { echo "Postgres connection test failed."; exit 1; }
}

# Create the database
create_database() {
    echo "Creating database $DB_NAME..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE $DB_NAME;"
}

# Create the user
create_user() {
    echo "Creating user $DB_USER..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h 127.0.0.1 -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
}

# Grant privileges
grant_privileges() {
    echo "Granting privileges on database $DB_NAME to user $DB_USER..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h 127.0.0.1 -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h 127.0.0.1 -d $DB_NAME -c "GRANT ALL PRIVILEGES ON SCHEMA public TO $DB_USER;"
    PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -h 127.0.0.1 -d $DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;"
}

# Create vector extension as superuser
create_vector_extension() {
    echo "Creating vector extension..."
    sudo -u postgres psql -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"
}

# Connect to the database and create the table
create_table() {
    echo "Creating table in database $DB_NAME..."
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h 127.0.0.1 -c "
    CREATE TABLE IF NOT EXISTS task_memory (
        id SERIAL PRIMARY KEY,
        task TEXT NOT NULL,
        goals TEXT,
        personas JSONB,
        embedding VECTOR(768),
        reference_urls TEXT[]
    );
    "
}

# Function to alter the table to add reference_urls column
alter_table() {
    echo "Altering table in database $DB_NAME to add reference_urls column..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -U postgres -d $DB_NAME -h 127.0.0.1 -c "
    ALTER TABLE task_memory ADD COLUMN IF NOT EXISTS reference_urls TEXT[];
    "
}

# Function to drop the task_memory table if it exists
drop_table() {
    echo "Dropping table task_memory if it exists..."
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h 127.0.0.1 -c "DROP TABLE IF EXISTS task_memory;"
}

# Function to create the emotional_tones table
create_emotional_tones_table() {
    echo "Creating table emotional_tones in database $DB_NAME..."
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h 127.0.0.1 -c "
    CREATE TABLE IF NOT EXISTS emotional_tones (
        id SERIAL PRIMARY KEY,
        tone TEXT NOT NULL
    );
    "
}

# Connection Tests
test_database_connection() {
    echo "Testing database connection..."
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h 127.0.0.1 -c "\dt" || { echo "Connection test failed."; exit 1; }
    echo "Connection test successful."
}

# Query Test
test_table_query() {
    echo "Testing table creation..."
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h 127.0.0.1 -c "SELECT * FROM task_memory LIMIT 1;" || { echo "Table query test failed."; exit 1; }
    echo "Table query test successful."
}

# Main function
main() {
    while getopts ":ic" opt; do
        case $opt in
            i)
                echo "Installing PostgreSQL..."
                detect_os_and_install
                install_pgvector
                check_data_directory
                start_postgresql_service
                get_pg_hba_conf_location
                update_pg_hba_conf
                reload_postgresql_configuration
                set_postgres_password
                test_postgres_connection
                create_database
                create_user
                grant_privileges
                create_vector_extension
                drop_table  # Add this line to drop the table before creating it
                create_table
                alter_table  # Ensure the table is altered if it already exists
                create_emotional_tones_table  # Add this line to create the emotional_tones table
                test_database_connection
                test_table_query
                echo "Database setup and tests complete."
                ;;
            c)
                echo "Cleaning up PostgreSQL installation..."
                cleanup_database
                cleanup_postgresql
                ;;
            \?)
                echo "Invalid option: -$OPTARG"
                exit 1
                ;;
        esac
    done
}

main "$@"
