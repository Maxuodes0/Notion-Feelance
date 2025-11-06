import os
from notion_client import Client


def main():
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DB_ID")

    if not notion_token or not database_id:
        print("❌ Missing NOTION_TOKEN or NOTION_DB_ID environment variables.")
        return

    notion = Client(auth=notion_token)

    print(f"⏳ Querying Notion database: {database_id} ...")
    response = notion.databases.query(database_id=database_id, page_size=100)
    results = response.get("results", [])
    print(f"✅ Found {len(results)} items in the database.")

    # نمر على كل الصفوف ونحدث حالة الطلب
    for idx, page in enumerate(results, start=1):
        page_id = page.get("id")
        print(f"🔄 Updating page {idx} ({page_id}) -> حالة الطلب = قيد الانتظار")

        try:
            notion.pages.update(
                page_id=page_id,
                properties={
                    "حالة الطلب": {
                        "status": {"name": "قيد الانتظار"}
                    }
                }
            )
            print("✅ Updated successfully.")
        except Exception as e:
            print(f"⚠️ Failed to update page {idx}: {e}")

    print("\n🏁 Done. All pages updated to حالة الطلب = قيد الانتظار.")


if __name__ == "__main__":
    main()
