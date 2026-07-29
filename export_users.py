import csv
from datetime import datetime
import configparser

config = configparser.ConfigParser(inline_comment_prefixes="#")
config.read("config.ini")

def export_users_to_csv():
    try:
        try:
            import psycopg2
        except ImportError:
            print("❌ psycopg2 not installed. Trying alternative method...")
            import subprocess
            print("Using PostgreSQL command line tool...")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"usernames_{timestamp}.csv"

            psql_command = [
                'psql',
                '-h', config['DATABASE']['host'],
                '-p', str(config['DATABASE']['port']),
                '-U', config['DATABASE']['user'],
                '-d', config['DATABASE']['db'],
                '-c', "COPY (SELECT ROW_NUMBER() OVER (ORDER BY user_id) as num, '@' || username FROM users WHERE username IS NOT NULL AND username != '') TO STDOUT WITH CSV",
                '-o', filename
            ]

            env = {'PGPASSWORD': config['DATABASE']['pass']}

            result = subprocess.run(psql_command, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"\n✅ Successfully exported usernames to {filename}")
                return
            else:
                print(f"❌ Error: {result.stderr}")
                return

        print("Connecting to database...")

        conn = psycopg2.connect(
            user=config['DATABASE']['user'],
            host=config['DATABASE']['host'],
            password=config['DATABASE']['pass'],
            port=int(config['DATABASE']['port']),
            database=config['DATABASE']['db']
        )

        cursor = conn.cursor()

        cursor.execute("SELECT user_id, username FROM users WHERE username IS NOT NULL AND username != ''")
        users = cursor.fetchall()

        print(f"Found {len(users)} users with usernames in database")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"usernames_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            row_num = 1
            for user in users:
                user_id, username = user
                writer.writerow([row_num, f"@{username}"])
                row_num += 1

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        print(f"\n✅ Successfully exported {len(users)} usernames to {filename}")
        print(f"📊 Total users in DB: {total_users}")
        print(f"📊 Users with username: {len(users)}")
        print(f"📊 Users without username: {total_users - len(users)}")
        print(f"\n💡 You can open {filename} in Excel or convert to .xlsx format")

    except Exception as e:
        print(f"❌ Error exporting users: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 50)
    print("Export Usernames to CSV")
    print("=" * 50)
    export_users_to_csv()
