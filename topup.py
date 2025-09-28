def cari_riwayat_topup(user_id=None, status=None, tanggal=None, min_nominal=None, max_nominal=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = "SELECT id, nominal, status, waktu FROM topup WHERE 1=1"
    params = []
    if user_id:
        query += " AND user_id=?"
        params.append(user_id)
    if status:
        query += " AND status=?"
        params.append(status)
    if tanggal:
        query += " AND waktu LIKE ?"
        params.append(f"%{tanggal}%")
    if min_nominal:
        query += " AND nominal>=?"
        params.append(min_nominal)
    if max_nominal:
        query += " AND nominal<=?"
        params.append(max_nominal)
    query += " ORDER BY waktu DESC LIMIT 20"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows
