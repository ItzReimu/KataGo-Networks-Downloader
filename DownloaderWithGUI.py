import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import random
import string
import re
import threading
import os
from urllib.parse import urlparse
import webbrowser

class KataGoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("KataGo Networks Downloader")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        self.networks_data = []
        self.filtered_data = []
        self.download_dir = os.path.expanduser("~/Downloads")
        self.latest_network = None
        self.strongest_network = None
        self.create_widgets()
        self.load_networks()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        title_label = ttk.Label(main_frame, text="KataGo Networks Downloader", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="5")
        control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)

        self.refresh_btn = ttk.Button(control_frame, text="刷新网络列表", command=self.load_networks)
        self.refresh_btn.grid(row=0, column=0, padx=(0, 10))

        ttk.Label(control_frame, text="下载目录:").grid(row=0, column=1, sticky=tk.W)
        dir_frame = ttk.Frame(control_frame)
        dir_frame.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(5, 0))
        dir_frame.columnconfigure(0, weight=1)
        self.dir_var = tk.StringVar(value=self.download_dir)
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, state="readonly")
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(dir_frame, text="选择", command=self.select_directory).grid(row=0, column=1, padx=(5, 0))

        info_frame = ttk.LabelFrame(main_frame, text="特殊网络", padding="5")
        info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(2, weight=1)

        latest_frame = ttk.Frame(info_frame)
        latest_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        latest_frame.columnconfigure(0, weight=1)
        self.latest_label = ttk.Label(latest_frame, text="最新网络: 加载中...", foreground="blue")
        self.latest_label.grid(row=0, column=0, sticky=tk.W)
        self.latest_btn = ttk.Button(latest_frame, text="下载", state="disabled", command=self._download_latest_network)
        self.latest_btn.grid(row=0, column=1, padx=(5, 0))

        separator = ttk.Separator(info_frame, orient='vertical')
        separator.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=10)

        strongest_frame = ttk.Frame(info_frame)
        strongest_frame.grid(row=0, column=2, sticky=(tk.W, tk.E))
        strongest_frame.columnconfigure(0, weight=1)
        self.strongest_label = ttk.Label(strongest_frame, text="最强网络: 加载中...", foreground="green")
        self.strongest_label.grid(row=0, column=0, sticky=tk.W)
        self.strongest_btn = ttk.Button(strongest_frame, text="下载", state="disabled", command=self._download_strongest_network)
        self.strongest_btn.grid(row=0, column=1, padx=(5, 0))

        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="搜索:").grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Label(search_frame, text="最小Elo:").grid(row=0, column=2, padx=(0, 5))
        self.min_elo_var = tk.StringVar()
        self.min_elo_var.trace('w', self.on_search_change)
        min_elo_entry = ttk.Entry(search_frame, textvariable=self.min_elo_var, width=10)
        min_elo_entry.grid(row=0, column=3, padx=(0, 10))
        ttk.Button(search_frame, text="清除筛选", command=self.clear_filters).grid(row=0, column=4)

        list_frame = ttk.LabelFrame(main_frame, text="网络列表", padding="5")
        list_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ("Name", "Time", "Elo", "Size", "Download")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        self.tree.heading("Name", text="网络名称")
        self.tree.heading("Time", text="更新时间")
        self.tree.heading("Elo", text="Elo评分")
        self.tree.heading("Size", text="文件大小")
        self.tree.heading("Download", text="下载链接")
        self.tree.column("Name", width=250, minwidth=180)
        self.tree.column("Time", width=150, minwidth=120)
        self.tree.column("Elo", width=100, minwidth=80)
        self.tree.column("Size", width=100, minwidth=80)
        self.tree.column("Download", width=350, minwidth=200)

        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))

        self.tree.bind("<Double-1>", self.on_item_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        ttk.Button(button_frame, text="下载选中", command=self.download_selected).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="复制链接", command=self.copy_link).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="在浏览器中打开", command=self.open_in_browser).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="调试信息", command=self.show_debug_info).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100, mode='determinate')
        self.create_context_menu()

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="下载", command=self.download_selected)
        self.context_menu.add_command(label="复制链接", command=self.copy_link)
        self.context_menu.add_command(label="在浏览器中打开", command=self.open_in_browser)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制网络名称", command=self.copy_name)

    def on_right_click(self, event):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            self.context_menu.post(event.x_root, event.y_root)

    def select_directory(self):
        directory = filedialog.askdirectory(initialdir=self.download_dir)
        if directory:
            self.download_dir = directory
            self.dir_var.set(directory)

    def load_networks(self):
        self.refresh_btn.configure(state="disabled", text="加载中...")
        self.status_var.set("正在获取网络列表...")
        for item in self.tree.get_children():
            self.tree.delete(item)
        threading.Thread(target=self._fetch_networks, daemon=True).start()

    def _fetch_networks(self):
        try:
            url = "https://katagotraining.org/networks/"
            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
                "cache-control": "max-age=0",
                "csrftoken": ''.join(random.choices(string.ascii_letters + string.digits, k=40)),
                "dnt": "1",
                "priority": "u=0, i",
                "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            self.debug_html = response.text

            latest_match = re.search(r'Latest network:</span>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', response.text)
            strongest_match = re.search(r'Strongest confidently-rated network:</span>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', response.text)

            if not latest_match:
                latest_match = re.search(r'Latest network:\s*<[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', response.text)
            if not strongest_match:
                strongest_match = re.search(r'Strongest confidently-rated network:\s*<[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', response.text)

            pattern = re.compile(r'<td>\s*(kata1-[^<\s]+)\s*</td>\s*<td>\s*([^<]+UTC)\s*</td>\s*<td>\s*([^<]+?)\s*</td>\s*<td>\s*<a href="([^"]+?\.bin\.gz)"', re.S)
            matches = pattern.findall(response.text)

            self.root.after(0, self._update_ui, latest_match, strongest_match, matches)
        except Exception as e:
            self.root.after(0, self._handle_error, str(e))

    def _update_ui(self, latest_match, strongest_match, matches):
        try:
            if latest_match:
                self.latest_network = latest_match
                latest_name = latest_match.group(2).strip()
                self.latest_label.configure(text=f"最新网络: {latest_name}")
                self.latest_btn.configure(state="normal")
            else:
                self.latest_network = None
                self.latest_label.configure(text="最新网络: 未找到")
                self.latest_btn.configure(state="disabled")

            if strongest_match:
                self.strongest_network = strongest_match
                strongest_name = strongest_match.group(2).strip()
                self.strongest_label.configure(text=f"最强网络: {strongest_name}")
                self.strongest_btn.configure(state="normal")
            else:
                self.strongest_network = None
                self.strongest_label.configure(text="最强网络: 未找到")
                self.strongest_btn.configure(state="disabled")

            self.networks_data = []
            for name, time_str, elo, link in matches:
                size_info = "获取中..."
                self.networks_data.append({
                    'name': name.strip(),
                    'time': time_str.strip(),
                    'elo': elo.strip(),
                    'link': link,
                    'size': size_info
                })

            self.update_tree_view()
            threading.Thread(target=self._fetch_file_sizes, daemon=True).start()
            self.status_var.set(f"成功加载 {len(matches)} 个网络")
        except Exception as e:
            print(f"DEBUG: _update_ui 发生错误: {e}")
            self._handle_error(str(e))
        finally:
            self.refresh_btn.configure(state="normal", text="刷新网络列表")

    def _fetch_file_sizes(self):
        for i, network in enumerate(self.networks_data):
            try:
                response = requests.head(network['link'], timeout=10)
                if 'content-length' in response.headers:
                    size_bytes = int(response.headers['content-length'])
                    size_mb = size_bytes / (1024 * 1024)
                    network['size'] = f"{size_mb:.1f} MB"
                else:
                    network['size'] = "未知"
            except:
                network['size'] = "未知"
            if i % 10 == 0:
                self.root.after(0, self.update_tree_view)
        self.root.after(0, self.update_tree_view)

    def _download_latest_network(self):
        if self.latest_network:
            name = self.latest_network.group(2)
            link = self.latest_network.group(1)
            filename = os.path.basename(link)
            threading.Thread(target=self.download_file, args=(link, filename), daemon=True).start()
        else:
            messagebox.showwarning("警告", "最新网络信息不可用")

    def _download_strongest_network(self):
        if self.strongest_network:
            name = self.strongest_network.group(2)
            link = self.strongest_network.group(1)
            filename = os.path.basename(link)
            threading.Thread(target=self.download_file, args=(link, filename), daemon=True).start()
        else:
            messagebox.showwarning("警告", "最强网络信息不可用")

    def _handle_error(self, error_msg):
        self.status_var.set(f"错误: {error_msg}")
        self.refresh_btn.configure(state="normal", text="刷新网络列表")
        messagebox.showerror("错误", f"获取网络列表失败:\n{error_msg}")

    def on_search_change(self, *args):
        self.update_tree_view()

    def clear_filters(self):
        self.search_var.set("")
        self.min_elo_var.set("")

    def update_tree_view(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_text = self.search_var.get().lower()
        min_elo_text = self.min_elo_var.get().strip()
        filtered_data = []
        for network in self.networks_data:
            if search_text and search_text not in network['name'].lower():
                continue
            if min_elo_text:
                try:
                    min_elo = float(min_elo_text)
                    network_elo = float(network['elo']) if network['elo'].replace('.', '').replace('-', '').isdigit() else 0
                    if network_elo < min_elo:
                        continue
                except ValueError:
                    pass
            filtered_data.append(network)

        for network in filtered_data:
            self.tree.insert("", "end", values=(
                network['name'],
                network['time'],
                network['elo'],
                network['size'],
                network['link']
            ))
        self.filtered_data = filtered_data

    def on_item_double_click(self, event):
        self.download_selected()

    def download_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要下载的网络")
            return
        for item in selection:
            values = self.tree.item(item)['values']
            name, link = values[0], values[4]
            filename = os.path.basename(link)
            threading.Thread(target=self.download_file, args=(link, filename), daemon=True).start()

    def download_file(self, url, filename):
        try:
            filepath = os.path.join(self.download_dir, filename)
            if os.path.exists(filepath):
                result = messagebox.askyesno("文件已存在", f"文件 {filename} 已存在，是否覆盖？")
                if not result:
                    return
            self.root.after(0, lambda: self.status_var.set(f"正在下载: {filename}"))
            self.root.after(0, self._show_progress_bar)

            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            def format_size(size_bytes):
                if size_bytes == 0:
                    return "0 B"
                size_names = ["B", "KB", "MB", "GB"]
                i = 0
                while size_bytes >= 1024 and i < len(size_names) - 1:
                    size_bytes /= 1024
                    i += 1
                return f"{size_bytes:.1f} {size_names[i]}"

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            downloaded_str = format_size(downloaded_size)
                            total_str = format_size(total_size)
                            self.root.after(0, lambda p=progress: self.progress_var.set(p))
                            self.root.after(0, lambda: self.status_var.set(
                                f"正在下载 {filename}: {downloaded_str}/{total_str} ({progress:.1f}%)"
                            ))
                        else:
                            downloaded_str = format_size(downloaded_size)
                            self.root.after(0, lambda: self.status_var.set(
                                f"正在下载 {filename}: {downloaded_str}"
                            ))

            final_size = format_size(downloaded_size)
            self.root.after(0, self._download_success, filename, filepath, final_size)
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, self._download_error, filename, error_msg)

    def _download_success(self, filename, filepath, final_size):
        self._hide_progress_bar()
        self.status_var.set(f"下载完成: {filename} ({final_size})")
        messagebox.showinfo("成功", f"文件已下载到:\n{filepath}\n文件大小: {final_size}")

    def _download_error(self, filename, error_msg):
        self._hide_progress_bar()
        self.status_var.set(f"下载失败: {filename}")
        messagebox.showerror("下载失败", f"下载 {filename} 失败:\n{error_msg}")

    def _show_progress_bar(self):
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        self.progress_var.set(0)

    def _hide_progress_bar(self):
        self.progress_bar.grid_remove()

    def copy_link(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个网络")
            return
        values = self.tree.item(selection[0])['values']
        link = values[4]
        self.root.clipboard_clear()
        self.root.clipboard_append(link)
        self.status_var.set("链接已复制到剪贴板")

    def copy_name(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个网络")
            return
        values = self.tree.item(selection[0])['values']
        name = values[0]
        self.root.clipboard_clear()
        self.root.clipboard_append(name)
        self.status_var.set("网络名称已复制到剪贴板")

    def open_in_browser(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个网络")
            return
        values = self.tree.item(selection[0])['values']
        link = values[4]
        webbrowser.open(link)
        self.status_var.set("已在浏览器中打开链接")

    def show_debug_info(self):
        if not hasattr(self, 'debug_html'):
            messagebox.showinfo("调试", "请先刷新网络列表以获取调试信息")
            return
        debug_window = tk.Toplevel(self.root)
        debug_window.title("调试信息")
        debug_window.geometry("800x600")

        text_frame = ttk.Frame(debug_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        html_content = self.debug_html
        latest_section = re.search(r'Latest network:.*?</a>', html_content, re.DOTALL)
        strongest_section = re.search(r'Strongest confidently-rated network:.*?</a>', html_content, re.DOTALL)
        debug_text = "=== 调试信息 ===\n"
        if latest_section:
            debug_text += "Latest network:\n"
            debug_text += latest_section.group(0) + "\n"
        else:
            debug_text += "未找到Latest network\n"
        if strongest_section:
            debug_text += "Strongest network HTML:\n"
            debug_text += strongest_section.group(0) + "\n"
        else:
            debug_text += "未找到Strongest network HTML片段\n"

        table_matches = re.findall(r'<tr[^>]*>.*?</tr>', html_content, re.DOTALL)[:5]
        for i, match in enumerate(table_matches):
            debug_text += f"行 {i+1}: {match[:200]}...\n"

        text_widget.insert(tk.END, debug_text)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def main():
    root = tk.Tk()
    app = KataGoDownloader(root)
    # 添加GitHub链接的标签
    github_label = ttk.Label(root, text="GitHub: https://github.com/ItzReimu/KataGo-Networks-Downloader", foreground="blue", cursor="hand2")
    github_label.grid(row=8, column=0, columnspan=3, pady=(5, 0))
    github_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/ItzReimu/KataGo-Networks-Downloader"))
    root.mainloop()

if __name__ == "__main__":
    main()
