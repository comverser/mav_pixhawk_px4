use mavlink::ardupilotmega::MavMessage;
use std::{
    collections::{HashMap, HashSet},
    time::Instant,
};

/// Extract the message type name from a MAVLink message
pub fn extract_message_type(msg: &MavMessage) -> String {
    format!("{msg:?}")
        .split('(')
        .next()
        .unwrap_or("UNKNOWN")
        .to_string()
}

/// Build a message filter from a list of message names
pub fn build_message_filter(messages: Option<Vec<String>>) -> Option<HashSet<String>> {
    messages.map(|msgs| msgs.iter().map(|s| s.trim().to_uppercase()).collect())
}

/// Track message frequencies over time
pub struct FrequencyTracker {
    last_times: HashMap<String, Instant>,
}

impl FrequencyTracker {
    pub fn new() -> Self {
        Self {
            last_times: HashMap::new(),
        }
    }

    pub fn calculate(&mut self, msg: &MavMessage) -> Option<f64> {
        let now = Instant::now();
        let msg_type = extract_message_type(msg);

        let frequency = self.last_times.get(&msg_type).map(|last| {
            let interval = now.duration_since(*last).as_secs_f64();
            if interval > 0.0 {
                1.0 / interval
            } else {
                0.0
            }
        });

        self.last_times.insert(msg_type, now);
        frequency
    }
}
