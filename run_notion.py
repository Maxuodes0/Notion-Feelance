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
    response = notion.databases.query(
        database_id=database_id,
        page_size=10
    )

    results = response.get("results", [])
    print(f"✅ Found {len(results)} items in the database.")

    for idx, page in enumerate(results, start=1):
        page_id = page.get("id")
        props = page.get("properties", {})

        print(f"\n[{idx}] Page ID: {page_id}")
        print("Properties:")

        for prop_name, prop_value in props.items():
            value_text = extract_property_text(prop_value)
            print(f"  - {prop_name}: {value_text}")


def extract_property_text(prop):
    prop_type = prop.get("type")

    if prop_type == "title":
        return "".join(t.get("plain_text", "") for t in prop.get("title", []))
    if prop_type == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
    if prop_type == "number":
        return str(prop.get("number"))
    if prop_type == "select":
        s = prop.get("select")
        return s.get("name") if s else ""
    if prop_type == "multi_select":
        return ", ".join(o.get("name", "") for o in prop.get("multi_select", []))
    if prop_type == "people":
        return ", ".join(p.get("name", "") for p in prop.get("people", []))
    if prop_type == "checkbox":
        return "✅" if prop.get("checkbox") else "❌"
    if prop_type == "date":
        d = prop.get("date") or {}
        return f"{d.get('start', '')} -> {d.get('end', '')}"
    if prop_type == "status":
        s = prop.get("status")
        return s.get("name") if s else ""
    if prop_type == "url":
        return prop.get("url", "")
    if prop_type == "email":
        return prop.get("email", "")
    if prop_type == "phone_number":
        return prop.get("phone_number", "")

    # أي نوع غير مغطى
    return ""


if __name__ == "__main__":
    main()
