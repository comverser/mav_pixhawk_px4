use crate::connection::MavConn;
use mavlink::{
    MavHeader,
    ardupilotmega::{
        HEARTBEAT_DATA, MavAutopilot, MavMessage, MavModeFlag, MavState, MavType,
        PARAM_REQUEST_LIST_DATA, REQUEST_DATA_STREAM_DATA,
    },
};
use std::{thread, time::Duration};

// MAVLink configuration constants
const TARGET_SYSTEM: u8 = 1;
const TARGET_COMPONENT: u8 = 1;
const STREAM_RATE_HZ: u16 = 10;
const HEARTBEAT_INTERVAL: Duration = Duration::from_secs(1);

/// Initialize vehicle connection by requesting parameters and data stream
pub fn initialize(vehicle: &MavConn) {
    send_message(vehicle, &create_param_request());
    send_message(vehicle, &create_stream_request());
}

/// Start background heartbeat thread
pub fn start_heartbeat(vehicle: &MavConn) {
    let vehicle = vehicle.clone();
    thread::spawn(move || {
        loop {
            send_heartbeat(&vehicle);
            thread::sleep(HEARTBEAT_INTERVAL);
        }
    });
}

fn send_message(vehicle: &MavConn, msg: &MavMessage) {
    if let Err(e) = vehicle.send(&MavHeader::default(), msg) {
        eprintln!("Send failed: {e}");
    }
}

fn send_heartbeat(vehicle: &MavConn) {
    if let Err(e) = vehicle.send_default(&create_heartbeat()) {
        eprintln!("Heartbeat failed: {e:?}");
    }
}
fn create_heartbeat() -> MavMessage {
    MavMessage::HEARTBEAT(HEARTBEAT_DATA {
        custom_mode: 0,
        mavtype: MavType::MAV_TYPE_QUADROTOR,
        autopilot: MavAutopilot::MAV_AUTOPILOT_ARDUPILOTMEGA,
        base_mode: MavModeFlag::empty(),
        system_status: MavState::MAV_STATE_STANDBY,
        mavlink_version: 0x3,
    })
}

fn create_param_request() -> MavMessage {
    MavMessage::PARAM_REQUEST_LIST(PARAM_REQUEST_LIST_DATA {
        target_system: TARGET_SYSTEM,
        target_component: TARGET_COMPONENT,
    })
}

fn create_stream_request() -> MavMessage {
    #[allow(deprecated)]
    MavMessage::REQUEST_DATA_STREAM(REQUEST_DATA_STREAM_DATA {
        target_system: TARGET_SYSTEM,
        target_component: TARGET_COMPONENT,
        req_stream_id: 0,
        req_message_rate: STREAM_RATE_HZ,
        start_stop: 1,
    })
}
