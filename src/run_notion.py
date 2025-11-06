import os
from notion_client import Client


def main():
    # ناخذ القيم من الـ environment variables
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DB_ID")

    if not notion_token or not database_id:
        print("❌ Missing NOTION_TOKEN or NOTION_DB_ID environment variables.")
        print("تأكد إنك ضايفهم كـ Secrets في GitHub أو كـ env محلياً.")
        return

    # إنشاء عميل نوشن
    notion = Client(auth=notion_token)

    # نقرأ أول 10 عناصر من قاعدة البيانات
    print(f"⏳ Querying Notion database: {database_id} ...")
    response = notion.databases.query(
        database_id=database_id,
        page_size=10
    )

    results = response.get("results", [])
    print(f"✅ Found {len(results)} items in the database.")

    # نحاول نطبع الاسم لو فيه property اسمه "Name"
    for idx, page in enumerate(results, start=1):
        properties = page.get("properties", {})
        name_text = None

        if "Name" in properties:
            name_prop = properties["Name"]
            title = name_prop.get("title", [])
            name_text = "".join([t.get("plain_text", "") for t in title])

        page_id = page.get("id")
        print(f"[{idx}] {name_text or page_id}")


if __name__ == "__main__":
    main()

