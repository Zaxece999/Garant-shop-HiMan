import csv
from datetime import datetime
import configparser
import subprocess
import os

config = configparser.ConfigParser(inline_comment_prefixes="#")
config.read("config.ini")

def export_users():
    print("Connecting to database...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"usernames_{timestamp}.csv"
    temp_output = "temp_output.txt"

    sql_query = "SELECT username FROM users WHERE username IS NOT NULL AND username != '' ORDER BY user_id"

    cmd = f'psql -h {config["DATABASE"]["host"]} -p {config["DATABASE"]["port"]} -U {config["DATABASE"]["user"]} -d {config["DATABASE"]["db"]} -t -A -c "{sql_query}"'

    env = os.environ.copy()
    env['PGPASSWORD'] = config['DATABASE']['pass']

    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"❌ Database error: {stderr.decode('utf-8')}")
            return

        usernames = []
        for line in stdout.decode('utf-8').split('\n'):
            line = line.strip()
            if line:
                usernames.append(line)

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for idx, username in enumerate(usernames, 1):
                writer.writerow([idx, f"@{username}"])

        print(f"\n✅ Successfully exported {len(usernames)} usernames")
        print(f"📁 File: {filename}")
        print(f"💡 You can open this file in Excel")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 50)
    print("Export Usernames to CSV")
    print("=" * 50)
    export_users()
