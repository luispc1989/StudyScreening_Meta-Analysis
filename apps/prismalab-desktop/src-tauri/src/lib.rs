#[tauri::command]
fn app_shell_status() -> &'static str {
    "PrismaLab desktop shell ready"
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![app_shell_status])
        .run(tauri::generate_context!())
        .expect("error while running PrismaLab desktop shell");
}
