#!/usr/bin/env python3
"""
MySQL Connection Fix Script
This script tests and fixes MySQL connectivity issues
"""

import os
import sys
import time
import subprocess
from dotenv import load_dotenv

def test_mysql_connection():
    """Test direct MySQL connection"""
    print("\n🔍 Testing MySQL connection...")
    
    try:
        import mysql.connector
        
        # Load environment variables
        load_dotenv()
        
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
        mysql_user = os.getenv('MYSQL_USER', 'root')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
        
        print(f"Connecting to MySQL at {mysql_host}:{mysql_port} as {mysql_user}...")
        
        # Try to connect to MySQL server (without specifying a database)
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            connection_timeout=5
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print(f"✅ MySQL connection successful! Version: {version}")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_database():
    """Create the dealnews database"""
    print("\n🛠️ Creating database...")
    
    try:
        import mysql.connector
        
        # Load environment variables
        load_dotenv()
        
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
        mysql_user = os.getenv('MYSQL_USER', 'root')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
        mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
        
        # Connect to MySQL server
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            connection_timeout=5
        )
        
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_database}")
        print(f"✅ Database '{mysql_database}' created/verified")
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Database creation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_mysql_process():
    """Check if MySQL is running"""
    print("\n🔍 Checking if MySQL is running...")
    
    try:
        # Check for MySQL process
        if sys.platform == 'darwin':  # macOS
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'mysqld' in result.stdout:
                print("✅ MySQL process is running")
                return True
            else:
                print("❌ MySQL process not found")
                return False
        elif sys.platform.startswith('linux'):
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'mysqld' in result.stdout:
                print("✅ MySQL process is running")
                return True
            else:
                print("❌ MySQL process not found")
                return False
        else:
            print("⚠️ Cannot check MySQL process on this platform")
            return None
            
    except Exception as e:
        print(f"❌ Error checking MySQL process: {e}")
        return None

def check_docker_mysql():
    """Check if MySQL is running in Docker"""
    print("\n🔍 Checking for MySQL in Docker...")
    
    try:
        # Check for Docker MySQL containers
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            if 'mysql' in result.stdout.lower():
                print("✅ MySQL container is running in Docker")
                
                # Get container name
                lines = result.stdout.strip().split('\n')
                mysql_container = None
                for line in lines[1:]:  # Skip header
                    if 'mysql' in line.lower():
                        parts = line.split()
                        mysql_container = parts[-1]  # Last column is name
                        break
                
                if mysql_container:
                    print(f"   Container name: {mysql_container}")
                    
                    # Update .env to use Docker container
                    update_env_for_docker(mysql_container)
                
                return True
            else:
                print("❌ No MySQL container found in Docker")
                return False
        else:
            print("⚠️ Docker not available or not running")
            return None
            
    except FileNotFoundError:
        print("⚠️ Docker command not found")
        return None
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return None

def update_env_for_docker(container_name):
    """Update .env file to use Docker MySQL"""
    print("\n🔧 Updating .env for Docker MySQL...")
    
    try:
        # Load current .env
        load_dotenv()
        
        # Check if .env exists
        env_file = '.env'
        if not os.path.exists(env_file):
            # Try to copy from template
            if os.path.exists('.env-template'):
                with open('.env-template', 'r') as src, open(env_file, 'w') as dst:
                    dst.write(src.read())
                print("✅ Created .env from .env-template")
            elif os.path.exists('env.example'):
                with open('env.example', 'r') as src, open(env_file, 'w') as dst:
                    dst.write(src.read())
                print("✅ Created .env from env.example")
            else:
                # Create minimal .env
                with open(env_file, 'w') as f:
                    f.write("# DealNews Scraper Environment\n")
                    f.write("MYSQL_HOST=host.docker.internal\n")
                    f.write("MYSQL_PORT=3306\n")
                    f.write("MYSQL_USER=root\n")
                    f.write("MYSQL_PASSWORD=root\n")
                    f.write("MYSQL_DATABASE=dealnews\n")
                    f.write("DISABLE_PROXY=true\n")
                    f.write("DISABLE_MYSQL=false\n")
                    f.write("CAPTURE_MODE=full\n")
                    f.write("LOG_LEVEL=WARNING\n")
                print("✅ Created new .env file")
        
        # Read current .env
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update MySQL settings
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith('MYSQL_HOST='):
                new_lines.append('MYSQL_HOST=host.docker.internal\n')
                updated = True
            elif line.startswith('DISABLE_MYSQL='):
                new_lines.append('DISABLE_MYSQL=false\n')
                updated = True
            else:
                new_lines.append(line)
        
        # Write updated .env
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        if updated:
            print("✅ Updated .env to use Docker MySQL")
        else:
            print("⚠️ No changes made to .env")
        
    except Exception as e:
        print(f"❌ Error updating .env: {e}")

def start_mysql_docker():
    """Start MySQL in Docker if possible"""
    print("\n🚀 Attempting to start MySQL in Docker...")
    
    try:
        # Check if Docker is available
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker not available")
            return False
        
        # Check if MySQL container exists but is stopped
        result = subprocess.run(['docker', 'ps', '-a'], capture_output=True, text=True)
        if 'mysql' in result.stdout.lower():
            print("Found existing MySQL container, starting it...")
            
            # Get container name
            lines = result.stdout.strip().split('\n')
            mysql_container = None
            for line in lines[1:]:  # Skip header
                if 'mysql' in line.lower():
                    parts = line.split()
                    mysql_container = parts[-1]  # Last column is name
                    break
            
            if mysql_container:
                # Start container
                subprocess.run(['docker', 'start', mysql_container])
                print(f"✅ Started MySQL container: {mysql_container}")
                
                # Wait for MySQL to be ready
                print("Waiting for MySQL to be ready...")
                time.sleep(10)
                
                # Update .env
                update_env_for_docker(mysql_container)
                
                return True
        
        # No existing container, try to run a new one
        print("Creating new MySQL container...")
        result = subprocess.run([
            'docker', 'run', '--name', 'dealnews-mysql',
            '-e', 'MYSQL_ROOT_PASSWORD=root',
            '-e', 'MYSQL_DATABASE=dealnews',
            '-p', '3306:3306',
            '-d', 'mysql:8.0'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Started new MySQL container")
            
            # Wait for MySQL to be ready
            print("Waiting for MySQL to be ready...")
            time.sleep(20)
            
            # Update .env
            update_env_for_docker('dealnews-mysql')
            
            return True
        else:
            print(f"❌ Failed to start MySQL container: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ Docker command not found")
        return False
    except Exception as e:
        print(f"❌ Error starting MySQL in Docker: {e}")
        return False

def check_env_file():
    """Check if .env file exists and is properly configured"""
    print("\n🔍 Checking .env file...")
    
    # Check if .env exists
    env_file = '.env'
    if os.path.exists(env_file):
        print("✅ .env file exists")
        
        # Load environment variables
        load_dotenv()
        
        # Check critical variables
        mysql_host = os.getenv('MYSQL_HOST')
        mysql_port = os.getenv('MYSQL_PORT')
        mysql_user = os.getenv('MYSQL_USER')
        mysql_password = os.getenv('MYSQL_PASSWORD')
        mysql_database = os.getenv('MYSQL_DATABASE')
        
        if not all([mysql_host, mysql_port, mysql_user, mysql_password, mysql_database]):
            print("❌ Missing critical MySQL variables in .env")
            return False
        
        print(f"✅ MySQL settings found: {mysql_host}:{mysql_port}")
        return True
    else:
        print("❌ .env file not found")
        
        # Try to copy from template
        if os.path.exists('.env-template'):
            with open('.env-template', 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Created .env from .env-template")
            return True
        elif os.path.exists('env.example'):
            with open('env.example', 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Created .env from env.example")
            return True
        
        print("❌ No template found to create .env")
        return False

def run_test_scraper():
    """Run a test scraper to verify everything works"""
    print("\n🕷️ Running test scraper...")
    
    try:
        # Run test_scraper_simple.py
        result = subprocess.run([sys.executable, 'test_scraper_simple.py'], 
                               capture_output=True, text=True)
        
        print(result.stdout)
        
        if "❌ Database connection failed" in result.stdout:
            print("❌ Database connection still failing")
            return False
        elif "✅ Database connected successfully" in result.stdout:
            print("✅ Database connection working!")
            return True
        else:
            print("⚠️ Unclear test result")
            return None
            
    except Exception as e:
        print(f"❌ Error running test scraper: {e}")
        return False

def main():
    print("=" * 60)
    print("DealNews Scraper - MySQL Connection Fix")
    print("=" * 60)
    
    # Step 1: Check .env file
    check_env_file()
    
    # Step 2: Check if MySQL is running
    mysql_running = check_mysql_process()
    
    # Step 3: Check for MySQL in Docker
    docker_mysql = check_docker_mysql()
    
    # Step 4: Test MySQL connection
    connection_ok = test_mysql_connection()
    
    # If connection failed, try to fix
    if not connection_ok:
        print("\n🔧 MySQL connection failed. Attempting fixes...")
        
        # If MySQL is not running, try to start it in Docker
        if mysql_running is False and docker_mysql is False:
            start_mysql_docker()
            
            # Wait for MySQL to be ready
            print("Waiting for MySQL to start...")
            time.sleep(15)
            
            # Test connection again
            connection_ok = test_mysql_connection()
    
    # If connection is now OK, create database
    if connection_ok:
        create_database()
        
        # Run test scraper
        run_test_scraper()
    
    # Final instructions
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    if connection_ok:
        print("✅ MySQL connection is working!")
        print("\nTo run the scraper:")
        print("1. Make sure .env is configured properly")
        print("2. Run: python3 run.py")
        print("   OR with Docker: docker-compose up scraper")
        print("\nIf you still have issues:")
        print("1. Set DISABLE_MYSQL=true in .env to skip database")
        print("2. Check the JSON export in exports/deals.json")
    else:
        print("❌ MySQL connection is still not working")
        print("\nTry these steps:")
        print("1. Install MySQL locally or use Docker")
        print("2. Update .env with correct MySQL settings")
        print("3. Set DISABLE_MYSQL=true in .env to run without database")
        print("4. Run: python3 run.py")
        print("\nTo use Docker for MySQL:")
        print("docker run --name dealnews-mysql -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=dealnews -p 3306:3306 -d mysql:8.0")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
