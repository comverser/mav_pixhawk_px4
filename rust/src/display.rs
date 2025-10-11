use crate::utils;
use mavlink::{
    ardupilotmega::{
        MavMessage, ATTITUDE_DATA, GLOBAL_POSITION_INT_DATA, HEARTBEAT_DATA, PARAM_VALUE_DATA,
    },
    MavHeader,
};
use std::collections::HashSet;

/// Display a MAVLink message with optional filtering
pub fn show(header: &MavHeader, msg: &MavMessage, filter: &Option<HashSet<String>>, frequency: Option<f64>) {
    if !should_display(msg, filter) {
        return;
    }

    let freq_str = frequency
        .map(|f| format!(" [{:>6.2} Hz]", f))
        .unwrap_or_else(|| String::from(" [---.-- Hz]"));

    match msg {
        MavMessage::HEARTBEAT(data) => print_heartbeat(header, data, &freq_str),
        MavMessage::ATTITUDE(data) => print_attitude(data, &freq_str),
        MavMessage::GLOBAL_POSITION_INT(data) => print_position(data, &freq_str),
        MavMessage::PARAM_VALUE(data) => print_parameter(data, &freq_str),
        _ => print_generic(header, msg, &freq_str),
    }
}

fn should_display(msg: &MavMessage, filter: &Option<HashSet<String>>) -> bool {
    let Some(allowed_messages) = filter else {
        return true;
    };

    let msg_type = utils::extract_message_type(msg);
    allowed_messages.contains(&msg_type)
}

fn print_heartbeat(header: &MavHeader, data: &HEARTBEAT_DATA, freq_str: &str) {
    println!(
        "HEARTBEAT [{}/{}] type={:?}, autopilot={:?}, state={:?}{}",
        header.system_id, header.component_id, data.mavtype, data.autopilot, data.system_status, freq_str
    );
}

fn print_attitude(data: &ATTITUDE_DATA, freq_str: &str) {
    println!(
        "ATTITUDE  roll={:>6.2}° pitch={:>6.2}° yaw={:>6.2}°{}",
        data.roll.to_degrees(),
        data.pitch.to_degrees(),
        data.yaw.to_degrees(),
        freq_str
    );
}

fn print_position(data: &GLOBAL_POSITION_INT_DATA, freq_str: &str) {
    println!(
        "POSITION  lat={:>10.6} lon={:>10.6} alt={:>7.1}m{}",
        data.lat as f64 / 1e7,
        data.lon as f64 / 1e7,
        data.alt as f64 / 1000.0,
        freq_str
    );
}

fn print_parameter(data: &PARAM_VALUE_DATA, freq_str: &str) {
    let name = String::from_utf8_lossy(&data.param_id)
        .trim_end_matches('\0')
        .to_string();
    println!("PARAM     {name} = {}{}", data.param_value, freq_str);
}

fn print_generic(header: &MavHeader, msg: &MavMessage, freq_str: &str) {
    let msg_type = utils::extract_message_type(msg);
    println!(
        "{msg_type} [{}/{}]{}",
        header.system_id, header.component_id, freq_str
    );
}
