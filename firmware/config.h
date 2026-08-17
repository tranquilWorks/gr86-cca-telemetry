#pragma once


// Customize your BLE device name here
#define DEVICE_NAME "CAN Telemetry"

// Firmware metadata
#define FW_VERSION "1.1.0-rc1"
#define FW_GITHASH "ble-twai-fix"

// Consumer BLE defaults: RaceChrono should connect without an iOS pairing dialog.
#define BLE_REQUIRE_PAIRING 0
// Let iOS choose stable connection parameters unless bench testing explicitly enables this.
#define BLE_REQUEST_FAST_CONN_PARAMS 0
// Physical CAN writes are compiled out; the controller remains in normal mode to ACK bench traffic.
#define CCA_ENABLE_CAN_TX_TEST 0

// GPS PPS discipline (set to -1 to disable)
#define GPS_PPS_GPIO 16

// Default divider for RaceChronoPidMap extra (only used as init)
#define DEFAULT_UPDATE_RATE_DIVIDER 10

// Enable NVS-backed configuration persistence helpers
#define ENABLE_CCA_CFG_NVS 1

// CAN bus baud rate (500 kbps)
static const long BAUD_RATE = 500 * 1000L;

// ---- Car profile selection ----
#include "pidmaps/pidmap_defs.h"
#include "pidmaps/gr86_2022.h"

static constexpr const pidmaps::PidMapDefinition *ACTIVE_PID_MAP = &pidmaps::GR86_2022;

