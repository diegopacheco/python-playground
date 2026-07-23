import distro


def main() -> None:
    print("id:", distro.id())
    print("name:", distro.name(pretty=True))
    print("version:", distro.version(pretty=True))
    print("major:", distro.major_version())
    print("codename:", distro.codename())
    print("like:", distro.like())
    print("info:", distro.info())


if __name__ == "__main__":
    main()
