def greet_user():
    name = input("Wie heisst du? ").strip()
    if name:
        print(f"Hi, {name}!")
    else:
        print("Hi!")


if __name__ == "__main__":
    greet_user()
