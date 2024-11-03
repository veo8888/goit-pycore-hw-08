import os
import pickle
from collections import UserDict
from datetime import datetime, timedelta
from colorama import Fore, Style, init

init()  # Ініціалізація colorama

def print_red(message):
    print(Fore.RED + message + Style.RESET_ALL)

def print_yellow(message):
    print(Fore.YELLOW + message + Style.RESET_ALL)

def print_green(message):
    print(Fore.GREEN + message + Style.RESET_ALL)

class Field:
    """Базовий клас для поля запису."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:  #Перевірка, чи є номер телефону з 10 цифр.
            raise ValueError("Phone number must be 10 digits.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return f"Phone {phone} removed."
        return f"Phone {phone} not found."
    
    def edit_phone(self, old_phone, new_phone):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return f"Phone {old_phone} updated to {new_phone}."
        return f"Phone {old_phone} not found."

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def days_to_birthday(self):
        if not self.birthday:
            print_red("Birthday not set.")
        today = datetime.today()
        next_birthday = self.birthday.value.replace(year=today.year)
        if next_birthday < today:
            next_birthday = next_birthday.replace(year=today.year + 1)
        return (next_birthday - today).days

    def __str__(self):
        phones_str = '; '.join(phone.value for phone in self.phones)
        birthday_str = f", birthday: {self.birthday.value.strftime('%d.%m.%Y')}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"

class AddressBook(UserDict):
    def add_record(self, record):  #Додає запис до книги. Якщо контакт вже є, додає новий номер
        existing_record = self.data.get(record.name.value)
        if existing_record:
            existing_record.phones.extend(record.phones)
        else:
            self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            print_green(f"Contact {name} deleted.")
            return
        print_red("Contact not found.")

    def get_upcoming_birthdays(self):
        today = datetime.today()
        next_week = today + timedelta(days=7)
        upcoming_birthdays = [
            f"{record.name.value}: {record.birthday.value.strftime('%d.%m.%Y')}"
            for record in self.data.values() if record.birthday and today <= record.birthday.value.replace(year=today.year) <= next_week
        ]
        return "Upcoming birthdays:\n" + "\n".join(upcoming_birthdays) if upcoming_birthdays else "No upcoming birthdays in the next 7 days."
    
    def save_to_file(self, filename="address_book.pkl"):
        with open(filename, "wb") as file:
            pickle.dump(self.data, file)

    def load_from_file(self, filename="address_book.pkl"):
        if os.path.exists(filename):  # Перевіряємо наявність файлу
            try:
                with open(filename, "rb") as file:
                    self.data = pickle.load(file)
            except (pickle.UnpicklingError, EOFError):  # Обробляємо помилки завантаження даних
                print_red("Error loading file. The file may be damaged.")
                self.data = {}  # Завантажуємо порожню книгу, якщо файл пошкоджено
        else:
            print_red("File not found, empty address book loaded.")

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            print_red("Contact not found.")

        except ValueError as e:
            print_red(str(e))
        except IndexError:
            print_red("Enter user name.")
    return inner

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

@input_error
def add_contact(args, address_book):
    if len(args) < 2:
        raise ValueError("Please provide name and phone please, separated by a space.")
    name, phone = args[0], args[1]
    record = Record(name)
    record.add_phone(phone)
    address_book.add_record(record)
    print_green(f"Contact {name} added with phone {phone}.")

@input_error
def add_birthday(args, book):
    if len(args) < 2:
        raise ValueError("Please provide name and date of birth, separated by a space.")
    name, birthday = args
    record = book.find(name)
    if record is None:
        print_red("Contact not found.")
    
    record.add_birthday(birthday)
    print_green(f"Birthday for {name} added.")

@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record is None or not record.birthday:
        print_red("No birthday found for this contact.")
    
    print_green(f"{name}'s birthday is on {record.birthday.value.strftime('%d.%m.%Y')}.")

@input_error
def birthdays(args, book):
    return book.get_upcoming_birthdays()

@input_error
def change_contact(args, address_book):
    if len(args) < 1:
        raise ValueError("Please provide the contact name.")

    name = args[0]
    record = address_book.find(name)

    if not record:
        print_red("Contact not found.")

    if not record.phones:
        print_red(f"No phones available for contact {name}.")

    phones_str = "\n".join(f"{i+1}. {phone.value}" for i, phone in enumerate(record.phones))  # Виводимо всі телефони контакту
    print(f"Current phones for {name}:\n{phones_str}")

    old_phone_index = int(input(Fore.YELLOW + "Enter the number of the phone you want to change (e.g., 1): " + Style.RESET_ALL)) - 1  # Просимо ввести номер, який потрібно змінити
    if old_phone_index < 0 or old_phone_index >= len(record.phones):
        print_red("Invalid phone selection.")
    old_phone = record.phones[old_phone_index].value

    new_phone = input(Fore.YELLOW + f"Enter the new phone number for {old_phone} (or leave blank to remove): " + Style.RESET_ALL)  # Запитуємо новий номер або порожнє введення для видалення номера
    result = record.edit_phone(old_phone, new_phone) if new_phone else record.remove_phone(old_phone)
    print_green(result)  # Виводимо результат

@input_error
def get_phone(args, address_book):
    if not args:
        raise IndexError
    name = args[0]
    record = address_book.find(name)
    if record:
        phones_str = '; '.join(phone.value for phone in record.phones)
        print_green(f"Phones for {name}: {phones_str}")
    else:
        raise KeyError
    
@input_error
def del_contact(args, address_book):
    if not args:
        raise IndexError
    name = args[0]
    return(address_book.delete(name))

@input_error
def show_all_contacts(address_book):
    if address_book:
        print("\n".join(str(record) for record in address_book.values()))
    else:
        print_red("Address book is empty.")

def main():
    address_book = AddressBook()
    address_book.load_from_file()  # Завантажуємо дані під час запуску

    print_yellow("Welcome to the assistant bot!") 
    print("""Supported Commands Menu:
# - hello --->         Greetings from Bot
# - add --->           Adding name and phone (Name Phone)
# - change --->        Edit, delete, phone (Name)
# - delete --->        Delete contact completely (Name)
# - phone --->         Show contact phone (Name)
# - all --->           Show all contacts
# - add-birthday --->  Add birthday to contact (Name)
# - show-birthday ---> Show contact's birthday (Name)
# - birthdays --->     Birthdays next 7 days
""")
    while True:
        user_input = input(Fore.YELLOW + "Enter a command: " + Style.RESET_ALL)
        if not user_input:
            print("Please enter a command.")
            continue
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print_green("Data saved.")
            address_book.save_to_file()  # Зберігаємо дані перед виходом
            print_yellow("Good bye!")
            break
        elif command == "hello":
            print_yellow("How can I help you?")
        elif command == "add":
            add_contact(args, address_book)
        elif command == "change":
            change_contact(args, address_book)
        elif command == "delete":
            del_contact(args, address_book)
        elif command == "phone":
            get_phone(args, address_book)
        elif command == "all":
            show_all_contacts(address_book)
        elif command == "add-birthday":
            add_birthday(args, address_book)
        elif command == "show-birthday":
            show_birthday(args, address_book)
        elif command == "birthdays":
            birthdays(args, address_book)
        else:
            print_red("""Invalid command.
Did you mean one of these:
add, change, delete, phone, all, add-birthday, show-birthday, birthdays.
""")

if __name__ == "__main__":
    main()
