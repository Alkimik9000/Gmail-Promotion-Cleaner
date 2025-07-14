from googleapiclient.discovery import build
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox

import config
import utils

load_dotenv()


def main():
    creds = utils.get_credentials()
    service = build("gmail", "v1", credentials=creds)

    senders_info = utils.get_unique_senders(service)
    items = list(senders_info.items())[: config.MAX_SENDERS]

    root = tk.Tk()
    root.title("Gmail Promotions Cleaner")

    tk.Label(root, text="Select senders to process:").pack()

    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(
        frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set, width=60, height=20
    )
    scrollbar.config(command=listbox.yview)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    for email, info in items:
        name = info["name"]
        count = info["count"]
        display = f"{name} <{email}> ({count})" if name else f"{email} ({count})"
        listbox.insert(tk.END, display)

    status = tk.Label(root, text="")
    status.pack(pady=5)

    def process(action: str):
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select at least one sender.")
            return
        msg = "unsubscribe and delete" if action == "unsubscribe" else "filter and delete"
        if not messagebox.askyesno(
            "Confirm", f"Are you sure you want to {msg} the selected senders?"
        ):
            return
        total = len(selected)
        for idx, i in enumerate(selected, 1):
            email_addr = items[i][0]
            status.config(text=f"Processing {idx}/{total}: {email_addr}")
            root.update_idletasks()
            try:
                if action == "unsubscribe":
                    utils.unsubscribe_sender(service, email_addr)
                else:
                    utils.create_filter(service, email_addr)
                utils.delete_emails_from_sender(service, email_addr)
            except Exception as e:
                print(f"Error processing {email_addr}: {e}")
        status.config(text="Done.")
        messagebox.showinfo("Completed", "Processing completed.")

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)

    tk.Button(
        btn_frame,
        text="Unsubscribe and Delete",
        command=lambda: process("unsubscribe"),
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Filter and Delete", command=lambda: process("filter")).pack(
        side=tk.LEFT, padx=5
    )

    root.mainloop()


if __name__ == "__main__":
    main()

