import os
from notion_client import Client


def extract_property_text(prop):
    """تحويل أي نوع من أنواع الـ property لنص بسيط."""
    prop_type = prop.get("type")

    if prop_type == "title":
        return "".join(t.get("plain_text", "") for t in prop.get("title", []))

    if prop_type == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))

    if prop_type == "number":
        number = prop.get("number")
        return "" if number is None else str(number)

    if prop_type == "select":
        s = prop.get("select")
        return s.get("name", "") if s else ""

    if prop_type == "multi_select":
        return ", ".join(o.get("name", "") for o in prop.get("multi_select", []))

    if prop_type == "people":
        return ", ".join(p.get("name", p.get("id", "")) for p in prop.get("people", []))

    if prop_type == "checkbox":
        return "✅" if prop.get("checkbox") else "❌"

    if prop_type == "date":
        d = prop.get("date") or {}
        start = d.get("start", "")
        end = d.get("end", "")
        if start and end:
            return f"{start} -> {end}"
        return start or end

    if prop_type == "status":
        s = prop.get("status")
        return s.get("name", "") if s else ""

    if prop_type == "url":
        return prop.get("url", "") or ""

    if prop_type == "email":
        return prop.get("email", "") or ""

    if prop_type == "phone_number":
        return prop.get("phone_number", "") or ""

    if prop_type == "files":
        return ", ".join(f.get("name", "") for f in prop.get("files", []))

    if prop_type == "relation":
        return ", ".join(r.get("id", "") for r in prop.get("relation", []))

    # أي نوع ما غطيناه
    return ""


def main():
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DB_ID")

    if not notion_token or not database_id:
        print("❌ Missing NOTION_TOKEN or NOTION_DB_ID environment variables.")
        return

    notion = Client(auth=notion_token)

    print(f"📄 Dumping all pages from database: {database_id}")

    has_more = True
    next_cursor = None
    total_pages = 0

    while has_more:
        query_args = {
            "database_id": database_id,
            "page_size": 100,
        }
        if next_cursor:
            query_args["start_cursor"] = next_cursor

        response = notion.databases.query(**query_args)

        results = response.get("results", [])
        has_more = response.get("has_more", False)
        next_cursor = response.get("next_cursor")

        for page in results:
            total_pages += 1
            page_id = page.get("id")
            props = page.get("properties", {})

            print(f"\n=== Page {total_pages} ===")
            print(f"ID: {page_id}")
            print("Properties:")

            for prop_name, prop_value in props.items():
                value_text = extract_property_text(prop_value)
                print(f"- {prop_name}: {value_text}")

    print(f"\n✅ Total pages found: {total_pages}")


if __name__ == "__main__":
    main()
