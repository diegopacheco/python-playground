import bleach

DIRTY = (
    '<p>hello <script>alert("xss")</script> '
    '<a href="javascript:evil()">click</a> <b>world</b></p>'
)


def main() -> None:
    allowed_tags = ["p", "b", "a"]
    allowed_attrs = {"a": ["href"]}
    clean = bleach.clean(DIRTY, tags=allowed_tags, attributes=allowed_attrs)
    print("dirty:", DIRTY)
    print("clean:", clean)
    print("stripped:", bleach.clean(DIRTY, tags=[], strip=True))
    print("linkified:", bleach.linkify("visit http://example.com now"))


if __name__ == "__main__":
    main()
