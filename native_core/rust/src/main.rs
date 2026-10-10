// Silicon Sanctuary — High-Performance Rust System Sentinel
// Architecture: Intel Gracemont Quad-Core & Win32 Telemetry Monitor

use std::env;
use std::time::Instant;

#[repr(C)]
#[derive(Debug, Default)]
struct MemoryStatusEx {
    dw_length: u32,
    dw_memory_load: u32,
    ull_total_phys: u64,
    ull_avail_phys: u64,
    ull_total_page_file: u64,
    ull_avail_page_file: u64,
    ull_total_virtual: u64,
    ull_avail_virtual: u64,
    ull_avail_extended_virtual: u64,
}

#[repr(C)]
#[derive(Debug, Default)]
struct FileTime {
    dw_low_date_time: u32,
    dw_high_date_time: u32,
}

#[link(name = "kernel32")]
extern "system" {
    fn GlobalMemoryStatusEx(lp_buffer: *mut MemoryStatusEx) -> i32;
    fn GetSystemTimes(
        lp_idle_time: *mut FileTime,
        lp_kernel_time: *mut FileTime,
        lp_user_time: *mut FileTime,
    ) -> i32;
}

fn file_time_to_u64(ft: &FileTime) -> u64 {
    ((ft.dw_high_date_time as u64) << 32) | (ft.dw_low_date_time as u64)
}

fn get_memory_stats() -> Option<MemoryStatusEx> {
    let mut mem = MemoryStatusEx {
        dw_length: std::mem::size_of::<MemoryStatusEx>() as u32,
        ..Default::default()
    };
    let res = unsafe { GlobalMemoryStatusEx(&mut mem) };
    if res != 0 {
        Some(mem)
    } else {
        None
    }
}

fn get_system_cpu_times() -> Option<(u64, u64, u64)> {
    let mut idle = FileTime::default();
    let mut kernel = FileTime::default();
    let mut user = FileTime::default();

    let res = unsafe { GetSystemTimes(&mut idle, &mut kernel, &mut user) };
    if res != 0 {
        Some((
            file_time_to_u64(&idle),
            file_time_to_u64(&kernel),
            file_time_to_u64(&user),
        ))
    } else {
        None
    }
}

fn sample_cpu_usage(interval_ms: u64) -> f64 {
    let (idle1, kernel1, user1) = match get_system_cpu_times() {
        Some(t) => t,
        None => return 0.0,
    };

    std::thread::sleep(std::time::Duration::from_millis(interval_ms));

    let (idle2, kernel2, user2) = match get_system_cpu_times() {
        Some(t) => t,
        None => return 0.0,
    };

    let idle_delta = idle2.saturating_sub(idle1);
    let kernel_delta = kernel2.saturating_sub(kernel1);
    let user_delta = user2.saturating_sub(user1);

    let total = kernel_delta + user_delta;
    if total == 0 {
        return 0.0;
    }

    let busy = total.saturating_sub(idle_delta);
    (busy as f64 / total as f64) * 100.0
}

fn print_telemetry_json() {
    let start = Instant::now();
    let mem = get_memory_stats();
    let cpu_load = sample_cpu_usage(80);
    let duration_us = start.elapsed().as_micros();

    let (mem_load, total_mb, avail_mb) = match mem {
        Some(m) => (
            m.dw_memory_load,
            m.ull_total_phys / (1024 * 1024),
            m.ull_avail_phys / (1024 * 1024),
        ),
        None => (0, 0, 0),
    };

    println!("{{");
    println!("  \"source\": \"rust_system_sentinel\",");
    println!("  \"status\": \"healthy\",");
    println!("  \"cpu_load_pct\": {:.2},", cpu_load);
    println!("  \"memory_load_pct\": {},", mem_load);
    println!("  \"total_ram_mb\": {},", total_mb);
    println!("  \"avail_ram_mb\": {},", avail_mb);
    println!("  \"used_ram_mb\": {},", total_mb.saturating_sub(avail_mb));
    println!("  \"telemetry_duration_us\": {}", duration_us);
    println!("}}");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() > 1 && args[1] == "--quick" {
        let mem = get_memory_stats().unwrap_or_default();
        let total_mb = mem.ull_total_phys / (1024 * 1024);
        let avail_mb = mem.ull_avail_phys / (1024 * 1024);
        println!(
            "{{\"ram_load\": {}, \"avail_mb\": {}, \"total_mb\": {}}}",
            mem.dw_memory_load, avail_mb, total_mb
        );
        return;
    }

    print_telemetry_json();
}
