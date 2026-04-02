import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'library.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 添加图书分类字段
try:
    cursor.execute("ALTER TABLE book ADD COLUMN category VARCHAR(50) DEFAULT '其他'")
    print("✅ 添加 category 字段")
except Exception as e:
    print(f"⚠️ category 字段: {e}")

# 添加用户状态字段
try:
    cursor.execute("ALTER TABLE user ADD COLUMN status VARCHAR(20) DEFAULT 'normal'")
    print("✅ 添加 status 字段")
except Exception as e:
    print(f"⚠️ status 字段: {e}")

# 添加用户创建时间
try:
    cursor.execute("ALTER TABLE user ADD COLUMN created_at TIMESTAMP")
    print("✅ 添加 created_at 字段")
except Exception as e:
    print(f"⚠️ created_at 字段: {e}")

# 添加图书借阅次数字段（用于排行榜）
try:
    cursor.execute("ALTER TABLE book ADD COLUMN borrow_count INTEGER DEFAULT 0")
    print("✅ 添加 borrow_count 字段")
except Exception as e:
    print(f"⚠️ borrow_count 字段: {e}")

# 添加借阅应还日期字段
try:
    cursor.execute("ALTER TABLE borrow_record ADD COLUMN due_date TIMESTAMP")
    print("✅ 添加 due_date 字段")
except Exception as e:
    print(f"⚠️ due_date 字段: {e}")

# 为现有未归还的借阅记录设置应还日期（30天后）
cursor.execute("UPDATE borrow_record SET due_date = datetime(borrow_date, '+30 days') WHERE due_date IS NULL AND status='borrowed'")
print("✅ 更新现有借阅记录的应还日期")

conn.commit()
conn.close()
print("\n🎉 数据库升级完成！")