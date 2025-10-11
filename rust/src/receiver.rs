use crate::{connection::MavConn, display, utils};
use mavlink::error::MessageReadError;
use std::{collections::HashSet, io::ErrorKind, thread, time::Duration};

const POLL_INTERVAL: Duration = Duration::from_millis(100);

/// Main message receiver loop
pub fn run(vehicle: &MavConn, filter: Option<HashSet<String>>) {
    println!("Listening for MAVLink messages...\n");

    let mut frequency_tracker = utils::FrequencyTracker::new();

    loop {
        match vehicle.recv() {
            Ok((header, msg)) => {
                let frequency = frequency_tracker.calculate(&msg);
                display::show(&header, &msg, &filter, frequency);
            }
            Err(e) if should_retry(&e) => {
                eprintln!("⏳ Waiting for data...");
                thread::sleep(POLL_INTERVAL);
            }
            Err(e) if is_connection_lost(&e) => {
                eprintln!("\n✗ Connection lost: {e}");
                break;
            }
            Err(e) => {
                eprintln!("✗ Message error: {e}");
            }
        }
    }
}

fn should_retry(error: &MessageReadError) -> bool {
    matches!(
        error,
        MessageReadError::Io(e) if e.kind() == ErrorKind::WouldBlock
    )
}

fn is_connection_lost(error: &MessageReadError) -> bool {
    matches!(error, MessageReadError::Io(_))
}
