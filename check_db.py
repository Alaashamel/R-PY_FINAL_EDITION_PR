#!/usr/bin/env python
"""Check database and cache status"""
import psycopg2
import redis

print("=" * 60)
print("HOSPITAL SYSTEM DATABASE CHECK")
print("=" * 60)

# PostgreSQL
print("\n[POSTGRESQL DATA]")
print("-" * 60)
try:
    conn = psycopg2.connect(
        host="localhost",
        database="hospital",
        user="postgres",
        password="postgres",
        port=5432
    )
    cur = conn.cursor()
    
    # Users
    cur.execute("SELECT id, username, email, is_admin, is_doctor FROM users ORDER BY id;")
    users = cur.fetchall()
    print("\n[USERS]")
    print(f"{'ID':<3} {'Username':<15} {'Email':<25} {'Admin':<6} {'Doctor':<6}")
    print("-" * 65)
    for row in users:
        print(f"{row[0]:<3} {row[1]:<15} {row[2]:<25} {str(row[3]):<6} {str(row[4]):<6}")
    
    # Doctors
    cur.execute("""
        SELECT d.id, u.username, d.first_name, d.last_name, d.specialization, d.is_active 
        FROM doctors d JOIN users u ON d.user_id = u.id ORDER BY d.id;
    """)
    doctors = cur.fetchall()
    print("\n[DOCTORS]")
    print(f"{'ID':<3} {'Username':<15} {'First':<10} {'Last':<10} {'Specialization':<20} {'Active':<6}")
    print("-" * 75)
    for row in doctors:
        print(f"{row[0]:<3} {row[1]:<15} {row[2]:<10} {row[3]:<10} {row[4]:<20} {str(row[5]):<6}")
    
    # Patients
    cur.execute("""
        SELECT p.id, u.username, p.first_name, p.last_name, p.phone 
        FROM patients p JOIN users u ON p.user_id = u.id ORDER BY p.id;
    """)
    patients = cur.fetchall()
    print("\n[PATIENTS]")
    print(f"{'ID':<3} {'Username':<15} {'First':<10} {'Last':<10} {'Phone':<15}")
    print("-" * 60)
    for row in patients:
        print(f"{row[0]:<3} {row[1]:<15} {row[2]:<10} {row[3]:<10} {str(row[4]):<15}")
    
    # Appointments
    cur.execute("""
        SELECT a.id, p.first_name || ' ' || p.last_name as patient,
               d.first_name || ' ' || d.last_name as doctor,
               a.appointment_date, a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.appointment_date DESC LIMIT 10;
    """)
    appts = cur.fetchall()
    print("\n[APPOINTMENTS] (last 10)")
    print(f"{'ID':<3} {'Patient':<20} {'Doctor':<20} {'Date':<25} {'Status':<10}")
    print("-" * 85)
    for row in appts:
        print(f"{row[0]:<3} {row[1]:<20} {row[2]:<20} {str(row[3])[:19]:<25} {row[4]:<10}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")

# Redis
print("\n\n" + "=" * 60)
print("[REDIS CACHE]")
print("-" * 60)
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    keys = r.keys('*')
    if keys:
        print(f"\nCached keys ({len(keys)} total):")
        for key in sorted(keys):
            ttl = r.ttl(key)
            val_len = len(r.get(key) or '')
            print(f"  {key:<40} (TTL: {ttl:>4}s, Size: {val_len} bytes)")
    else:
        print("\nNo cached data (cache is empty)")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
