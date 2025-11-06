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
    print(f"✅ Found {len(results)} items in the database.\n")

    updated_count = 0

    for idx, page in enumerate(results, start=1):
        page_id = page.get("id")
        props = page.get("properties", {})
        current_status = None

        # نحاول نقرأ قيمة حقل "حالة الطلب"
        if "حالة الطلب" in props:
            status_prop = props["حالة الطلب"]
            if status_prop.get("select"):
                current_status = status_prop["select"].get("name")

        print(f"[{idx}] Page ID: {page_id}")
        print(f"   الحالة الحالية: {current_status}")

        # إذا الحالة فاضية نحدّثها إلى "قيد الانتظار"
        if not current_status:
            print("   ➡️ Updating to 'قيد الانتظار' ...")
            try:
                notion.pages.update(
                    page_id=page_id,
                    properties={
                        "حالة الطلب": {"select": {"name": "قيد الانتظار"}}
                    }
                )
                updated_count += 1
                print("   ✅ Updated successfully.\n")
            except Exception as e:
                print(f"   ⚠️ Failed to update: {e}\n")
        else:
            print("   ⏭️ Skipped (already has a value)\n")

    print(f"🏁 Done. Updated {updated_count} pages to 'قيد الانتظار'.")


if __name__ == "__main__":
    main()
