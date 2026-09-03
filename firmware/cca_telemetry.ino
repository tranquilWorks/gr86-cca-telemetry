// ===== GR86 CCA Telemetry: stability-first RaceChrono bridge =====
//
// This sketch intentionally favors deterministic recovery over aggressive retries:
// - BLE advertising is event-driven and never stop/start-cycled from loop().
// - RaceChrono uses its standard unencrypted 0x1FF8 protocol (no passkey/token shim).
// - CAN is always accept-all at the controller; filtering happens in software.
// - CAN silence is normal. Only an actual TWAI fault triggers recovery.
// - CAN bring-up and recovery are non-blocking, so BLE/GPS/CLI stay alive.
// - CAN frames are coalesced by ID before BLE transmission to prevent backlog storms.
//
// Board: ESP32-S3 Dev Module
// Working regression toolchain: Arduino-ESP32 3.3.6 + NimBLE-Arduino 2.3.6

#include <Arduino.h>
#include <NimBLEDevice.h>
#include <Preferences.h>

#include <driver/twai.h>
#include <esp_err.h>
#include <esp_heap_caps.h>
#include <esp_system.h>
#include <esp_task_wdt.h>

#if defined(__has_include)
#  if __has_include(<esp_idf_version.h>)
#    include <esp_idf_version.h>
#  endif
#endif

#include <ctype.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "src/gps_nmea.h"
#include "src/led_status.h"
#include "src/nvs_cfg.h"

namespace cca {

// -----------------------------------------------------------------------------
// Build identity
// -----------------------------------------------------------------------------

static constexpr const char* BUILD_ID = "2.0.0-stability-20260902";

// -----------------------------------------------------------------------------
// Hardware pins
// -----------------------------------------------------------------------------

static constexpr int CAN_TX_GPIO = 5;
static constexpr int CAN_RX_GPIO = 4;

static constexpr int GPS_RX_GPIO = 18;  // GPS TX -> ESP RX
static constexpr int GPS_TX_GPIO = 17;  // GPS RX <- ESP TX

static constexpr int OIL_ADC_PIN = 1;

// -----------------------------------------------------------------------------
// RaceChrono DIY BLE UUIDs
// -----------------------------------------------------------------------------

static constexpr const char* RC_SERVICE_UUID =
    "00001ff8-0000-1000-8000-00805f9b34fb";
static constexpr const char* RC_CHAR_CAN_UUID =
    "00000001-0000-1000-8000-00805f9b34fb";
static constexpr const char* RC_CHAR_FILTER_UUID =
    "00000002-0000-1000-8000-00805f9b34fb";
static constexpr const char* RC_CHAR_GPS_UUID =
    "00000003-0000-1000-8000-00805f9b34fb";
static constexpr const char* RC_CHAR_GPS_TIME_UUID =
    "00000004-0000-1000-8000-00805f9b34fb";

// -----------------------------------------------------------------------------
// General helpers
// -----------------------------------------------------------------------------

static inline bool timeReached(uint32_t now, uint32_t deadline) {
  return static_cast<int32_t>(now - deadline) >= 0;
}

static inline uint32_t elapsedMs(uint32_t now, uint32_t then) {
  return now - then;
}

static inline float clampFloat(float value, float low, float high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

static const char* resetReasonName(esp_reset_reason_t reason) {
  switch (reason) {
    case ESP_RST_UNKNOWN:   return "UNKNOWN";
    case ESP_RST_POWERON:   return "POWERON";
    case ESP_RST_EXT:       return "EXT";
    case ESP_RST_SW:        return "SW";
    case ESP_RST_PANIC:     return "PANIC";
    case ESP_RST_INT_WDT:   return "INT_WDT";
    case ESP_RST_TASK_WDT:  return "TASK_WDT";
    case ESP_RST_WDT:       return "WDT";
    case ESP_RST_DEEPSLEEP: return "DEEPSLEEP";
    case ESP_RST_BROWNOUT:  return "BROWNOUT";
    case ESP_RST_SDIO:      return "SDIO";
#ifdef ESP_RST_USB
    case ESP_RST_USB:       return "USB";
#endif
#ifdef ESP_RST_JTAG
    case ESP_RST_JTAG:      return "JTAG";
#endif
#ifdef ESP_RST_CPU_LOCKUP
    case ESP_RST_CPU_LOCKUP:return "CPU_LOCKUP";
#endif
    default:                return "OTHER";
  }
}

static esp_reset_reason_t g_bootResetReason = ESP_RST_UNKNOWN;

// -----------------------------------------------------------------------------
// Watchdog
// -----------------------------------------------------------------------------

static void initWatchdog() {
  esp_err_t initResult = ESP_OK;

#if defined(ESP_IDF_VERSION_MAJOR) && (ESP_IDF_VERSION_MAJOR >= 5)
  esp_task_wdt_config_t config = {};
  config.timeout_ms = 5000;
  config.idle_core_mask = 0;
  config.trigger_panic = true;
  initResult = esp_task_wdt_init(&config);
#else
  initResult = esp_task_wdt_init(5, true);
#endif

  if (initResult != ESP_OK && initResult != ESP_ERR_INVALID_STATE) {
    Serial.printf("WARN: task watchdog init failed: %d\n",
                  static_cast<int>(initResult));
  }

  const esp_err_t addResult = esp_task_wdt_add(nullptr);
  if (addResult != ESP_OK && addResult != ESP_ERR_INVALID_STATE &&
      addResult != ESP_ERR_INVALID_ARG) {
    Serial.printf("WARN: task watchdog add failed: %d\n",
                  static_cast<int>(addResult));
  }
}

// -----------------------------------------------------------------------------
// Configuration and runtime filtering
// -----------------------------------------------------------------------------

static Preferences g_prefs;
static constexpr const char* CFG_NAMESPACE = "cca_cfg";

static bool g_profileEnabled = true;
static uint16_t g_oilPublishPeriodMs = 40;

struct __attribute__((packed)) StoredPidDivider {
  uint16_t pid;
  uint8_t divider;
};

static constexpr size_t MAX_CUSTOM_DIVIDERS = 64;

struct __attribute__((packed)) StoredDividerBlob {
  uint16_t count;
  StoredPidDivider items[MAX_CUSTOM_DIVIDERS];
};

static StoredPidDivider g_customDividers[MAX_CUSTOM_DIVIDERS] = {};
static uint16_t g_customDividerCount = 0;

static int customDividerIndex(uint32_t pid) {
  if (pid > 0xFFFFu) return -1;
  for (uint16_t i = 0; i < g_customDividerCount; ++i) {
    if (g_customDividers[i].pid == static_cast<uint16_t>(pid)) {
      return static_cast<int>(i);
    }
  }
  return -1;
}

static uint8_t customDividerFor(uint32_t pid) {
  const int index = customDividerIndex(pid);
  if (index < 0) return 0;
  uint8_t divider = g_customDividers[index].divider;
  return divider == 0 ? 1 : divider;
}

static bool setCustomDivider(uint32_t pid, uint8_t divider) {
  if (pid > 0x7FFu) return false;
  if (divider == 0) divider = 1;

  const int existing = customDividerIndex(pid);
  if (existing >= 0) {
    g_customDividers[existing].divider = divider;
    return true;
  }

  if (g_customDividerCount >= MAX_CUSTOM_DIVIDERS) return false;
  g_customDividers[g_customDividerCount].pid = static_cast<uint16_t>(pid);
  g_customDividers[g_customDividerCount].divider = divider;
  ++g_customDividerCount;
  return true;
}

static void clearCustomDividers() {
  memset(g_customDividers, 0, sizeof(g_customDividers));
  g_customDividerCount = 0;
}

static constexpr size_t MAX_DENIED_PIDS = 64;
static uint32_t g_deniedPids[MAX_DENIED_PIDS] = {};
static size_t g_deniedPidCount = 0;

static bool isDenied(uint32_t pid) {
  for (size_t i = 0; i < g_deniedPidCount; ++i) {
    if (g_deniedPids[i] == pid) return true;
  }
  return false;
}

static void denyPid(uint32_t pid) {
  if (isDenied(pid)) return;
  if (g_deniedPidCount < MAX_DENIED_PIDS) {
    g_deniedPids[g_deniedPidCount++] = pid;
  }
}

static void undenyPid(uint32_t pid) {
  for (size_t i = 0; i < g_deniedPidCount; ++i) {
    if (g_deniedPids[i] != pid) continue;
    for (size_t j = i + 1; j < g_deniedPidCount; ++j) {
      g_deniedPids[j - 1] = g_deniedPids[j];
    }
    --g_deniedPidCount;
    return;
  }
}

static void clearDeniedPids() {
  memset(g_deniedPids, 0, sizeof(g_deniedPids));
  g_deniedPidCount = 0;
}

struct RequestedPid {
  uint32_t pid;
  uint16_t intervalMs;
  bool used;
};

static constexpr size_t MAX_REQUESTED_PIDS = 128;
static RequestedPid g_requestedPids[MAX_REQUESTED_PIDS] = {};
static bool g_raceChronoFilterActive = false;
static bool g_raceChronoAllowAll = false;
static uint16_t g_raceChronoAllowAllIntervalMs = 0;
static uint32_t g_filterCommandCount = 0;

static void clearRaceChronoFilter() {
  memset(g_requestedPids, 0, sizeof(g_requestedPids));
  g_raceChronoFilterActive = false;
  g_raceChronoAllowAll = false;
  g_raceChronoAllowAllIntervalMs = 0;
}

static RequestedPid* findRequestedPid(uint32_t pid) {
  for (size_t i = 0; i < MAX_REQUESTED_PIDS; ++i) {
    if (g_requestedPids[i].used && g_requestedPids[i].pid == pid) {
      return &g_requestedPids[i];
    }
  }
  return nullptr;
}

static bool requestPid(uint32_t pid, uint16_t intervalMs) {
  if (RequestedPid* existing = findRequestedPid(pid)) {
    existing->intervalMs = intervalMs;
    return true;
  }

  for (size_t i = 0; i < MAX_REQUESTED_PIDS; ++i) {
    if (g_requestedPids[i].used) continue;
    g_requestedPids[i].pid = pid;
    g_requestedPids[i].intervalMs = intervalMs;
    g_requestedPids[i].used = true;
    return true;
  }

  return false;
}

static size_t requestedPidCount() {
  size_t count = 0;
  for (size_t i = 0; i < MAX_REQUESTED_PIDS; ++i) {
    if (g_requestedPids[i].used) ++count;
  }
  return count;
}

static uint8_t profileDividerFor(uint32_t pid) {
  const auto* map = ACTIVE_PID_MAP;
  if (map != nullptr) {
    for (size_t i = 0; i < map->ruleCount; ++i) {
      if (map->rules[i].pid == pid) {
        const uint8_t divider = map->rules[i].divider;
        return divider == 0 ? 1 : divider;
      }
    }
    if (map->policyDividerForId != nullptr) {
      const uint8_t divider = map->policyDividerForId(pid);
      if (divider != 0) return divider;
    }
  }

  return DEFAULT_UPDATE_RATE_DIVIDER == 0 ? 1
                                          : DEFAULT_UPDATE_RATE_DIVIDER;
}

static bool profileAllows(uint32_t pid) {
  const auto* map = ACTIVE_PID_MAP;
  if (map == nullptr || map->isCanIdWhitelisted == nullptr) return false;
  return map->isCanIdWhitelisted(pid);
}

struct RouteDecision {
  bool allowed;
  uint16_t minimumIntervalMs;
};

static RouteDecision routeDecision(uint32_t pid) {
  RouteDecision result = {false, 40};

  if (isDenied(pid)) return result;

  // A serial ALLOW command is an explicit operator override.
  const uint8_t customDivider = customDividerFor(pid);
  if (customDivider != 0) {
    result.allowed = true;
    uint32_t customInterval = static_cast<uint32_t>(customDivider) * 10u;
    if (customInterval < 10u) customInterval = 10u;
    if (customInterval > 2000u) customInterval = 2000u;
    result.minimumIntervalMs = static_cast<uint16_t>(customInterval);
    return result;
  }

  // PROFILE OFF is the deliberate bench/sniff mode. It ignores RaceChrono's
  // requested PID set but still honors the deny list and the BLE global cap.
  if (!g_profileEnabled) {
    result.allowed = true;
    result.minimumIntervalMs = 10;
    return result;
  }

  // Once RaceChrono sends a filter command, follow the standard protocol.
  if (g_raceChronoFilterActive) {
    if (g_raceChronoAllowAll) {
      result.allowed = true;
      result.minimumIntervalMs =
          g_raceChronoAllowAllIntervalMs == 0
              ? 10
              : g_raceChronoAllowAllIntervalMs;
      return result;
    }

    if (RequestedPid* requested = findRequestedPid(pid)) {
      result.allowed = true;
      result.minimumIntervalMs =
          requested->intervalMs == 0 ? 10 : requested->intervalMs;
      return result;
    }

    return result;
  }

  // Before RaceChrono sends filters, use the compiled GR86 profile so the
  // device still streams useful data in generic BLE clients.
  if (!profileAllows(pid)) return result;

  result.allowed = true;
  if (pid == 0x710u) {
    result.minimumIntervalMs = g_oilPublishPeriodMs;
  } else if (pid == 0x777u) {
    result.minimumIntervalMs = 2000;
  } else {
    const uint8_t divider = profileDividerFor(pid);
    uint32_t interval = static_cast<uint32_t>(divider) * 10u;
    // Cap per-ID output at 25 Hz even for profile entries with divider 1.
    if (interval < 40u) interval = 40u;
    if (interval > 2000u) interval = 2000u;
    result.minimumIntervalMs = static_cast<uint16_t>(interval);
  }

  return result;
}

static void loadRuntimeConfig() {
  g_profileEnabled = true;
  g_oilPublishPeriodMs = 40;
  clearCustomDividers();

  if (!g_prefs.begin(CFG_NAMESPACE, true)) return;

  if (g_prefs.isKey("profile")) {
    g_profileEnabled = g_prefs.getUChar("profile", 1) != 0;
  }

  if (g_prefs.isKey("oil_rate")) {
    const uint16_t storedRate = g_prefs.getUShort("oil_rate", 40);
    if (storedRate >= 10 && storedRate <= 2000) {
      g_oilPublishPeriodMs = storedRate;
    }
  }

  const size_t blobLength = g_prefs.getBytesLength("dividers");
  if (blobLength >= sizeof(uint16_t)) {
    StoredDividerBlob blob = {};
    const size_t readLength =
        g_prefs.getBytes("dividers", &blob, sizeof(blob));
    if (readLength >= sizeof(uint16_t)) {
      uint16_t count = blob.count;
      if (count > MAX_CUSTOM_DIVIDERS) count = MAX_CUSTOM_DIVIDERS;
      for (uint16_t i = 0; i < count; ++i) {
        if (blob.items[i].pid <= 0x7FFu) {
          setCustomDivider(blob.items[i].pid, blob.items[i].divider);
        }
      }
    }
  }

  g_prefs.end();
}

static bool saveRuntimeConfig() {
  if (!g_prefs.begin(CFG_NAMESPACE, false)) return false;
  ScopedNvsWrite writeGuard;

  bool ok = true;
  if (g_prefs.putUChar("profile", g_profileEnabled ? 1 : 0) !=
      sizeof(uint8_t)) {
    ok = false;
  }
  if (g_prefs.putUShort("oil_rate", g_oilPublishPeriodMs) !=
      sizeof(uint16_t)) {
    ok = false;
  }

  StoredDividerBlob blob = {};
  blob.count = g_customDividerCount;
  for (uint16_t i = 0; i < g_customDividerCount; ++i) {
    blob.items[i] = g_customDividers[i];
  }
  if (g_prefs.putBytes("dividers", &blob, sizeof(blob)) != sizeof(blob)) {
    ok = false;
  }

  g_prefs.end();
  return ok;
}

// -----------------------------------------------------------------------------
// BLE transport
// -----------------------------------------------------------------------------

static NimBLEServer* g_bleServer = nullptr;
static NimBLEAdvertising* g_bleAdvertising = nullptr;
static NimBLEService* g_bleService = nullptr;
static NimBLECharacteristic* g_canCharacteristic = nullptr;
static NimBLECharacteristic* g_filterCharacteristic = nullptr;
static NimBLECharacteristic* g_gpsCharacteristic = nullptr;
static NimBLECharacteristic* g_gpsTimeCharacteristic = nullptr;

static volatile bool g_bleConnected = false;
static volatile bool g_canSubscribed = false;
static volatile bool g_gpsSubscribed = false;
static volatile bool g_gpsTimeSubscribed = false;

static uint16_t g_bleMtu = 23;
static uint32_t g_bleConnectCount = 0;
static uint32_t g_bleDisconnectCount = 0;
static int g_lastBleDisconnectReason = 0;
static uint32_t g_lastBleConnectMs = 0;
static uint32_t g_lastBleDisconnectMs = 0;
static uint32_t g_advertisingStartCount = 0;
static uint32_t g_advertisingStartFailures = 0;
static uint32_t g_nextAdvertisingCheckMs = 0;

static uint32_t g_bleNotifySuccesses = 0;
static uint32_t g_bleNotifyFailures = 0;
static uint32_t g_bleNotifyRateDrops = 0;
static uint32_t g_bleNotifyUnsubscribedDrops = 0;
static uint32_t g_bleNotifyBackoffUntilMs = 0;
static uint32_t g_lastBleNotifyFailureMs = 0;

// Shared token bucket. GPS consumes ~11 notifications/s; the remaining budget
// is available for CAN. This prevents a noisy bus from starving NimBLE.
static constexpr uint16_t BLE_TOKEN_CAPACITY = 24;
static constexpr uint16_t BLE_TOKEN_RATE_PER_SECOND = 120;
static uint16_t g_bleTokens = BLE_TOKEN_CAPACITY;
static uint32_t g_bleTokenLastRefillMs = 0;

static bool isBleConnected() {
  return g_bleConnected && g_bleServer != nullptr &&
         g_bleServer->getConnectedCount() > 0;
}

static void refillBleTokens(uint32_t now) {
  if (g_bleTokenLastRefillMs == 0) {
    g_bleTokenLastRefillMs = now;
    g_bleTokens = BLE_TOKEN_CAPACITY;
    return;
  }

  const uint32_t elapsed = now - g_bleTokenLastRefillMs;
  if (elapsed == 0) return;

  const uint32_t add =
      (elapsed * static_cast<uint32_t>(BLE_TOKEN_RATE_PER_SECOND)) / 1000u;
  if (add == 0) return;

  uint32_t next = static_cast<uint32_t>(g_bleTokens) + add;
  if (next > BLE_TOKEN_CAPACITY) next = BLE_TOKEN_CAPACITY;
  g_bleTokens = static_cast<uint16_t>(next);

  const uint32_t consumedMs =
      (add * 1000u) / static_cast<uint32_t>(BLE_TOKEN_RATE_PER_SECOND);
  g_bleTokenLastRefillMs += consumedMs == 0 ? 1 : consumedMs;
}

static bool takeBleToken(uint32_t now) {
  refillBleTokens(now);
  if (g_bleTokens == 0) {
    ++g_bleNotifyRateDrops;
    return false;
  }
  --g_bleTokens;
  return true;
}

static bool notifyCharacteristic(NimBLECharacteristic* characteristic,
                                 bool subscribed,
                                 const uint8_t* data,
                                 size_t length,
                                 uint32_t now) {
  if (!isBleConnected() || characteristic == nullptr) return false;

  if (!subscribed) {
    ++g_bleNotifyUnsubscribedDrops;
    return false;
  }

  if (!timeReached(now, g_bleNotifyBackoffUntilMs)) return false;
  if (!takeBleToken(now)) return false;

  characteristic->setValue(data, length);
  if (characteristic->notify()) {
    ++g_bleNotifySuccesses;
    return true;
  }

  ++g_bleNotifyFailures;
  g_lastBleNotifyFailureMs = now;
  // A short quiet period is enough to let NimBLE drain. Do not restart BLE.
  g_bleNotifyBackoffUntilMs = now + 100;
  return false;
}

static void startAdvertisingIfNeeded(uint32_t now, bool forceCheck = false) {
  if (g_bleAdvertising == nullptr || isBleConnected()) return;
  if (!forceCheck && !timeReached(now, g_nextAdvertisingCheckMs)) return;

  g_nextAdvertisingCheckMs = now + 3000;
  if (g_bleAdvertising->isAdvertising()) return;

  if (g_bleAdvertising->start()) {
    ++g_advertisingStartCount;
    Serial.println("BLE: advertising");
  } else {
    ++g_advertisingStartFailures;
    Serial.println("WARN: BLE advertising start rejected; retry scheduled");
  }
}

class ServerCallbacks final : public NimBLEServerCallbacks {
 public:
  void onConnect(NimBLEServer*, NimBLEConnInfo& connInfo) override {
    g_bleConnected = true;
    g_canSubscribed = false;
    g_gpsSubscribed = false;
    g_gpsTimeSubscribed = false;
    g_bleMtu = connInfo.getMTU();
    g_lastBleConnectMs = millis();
    ++g_bleConnectCount;
    g_bleNotifyBackoffUntilMs = 0;
    g_bleTokens = BLE_TOKEN_CAPACITY;
    g_bleTokenLastRefillMs = millis();

    // RaceChrono sends a fresh filter set after connection.
    clearRaceChronoFilter();

    Serial.printf(
        "BLE: connected handle=%u interval=%.2fms timeout=%.2fs mtu=%u\n",
        static_cast<unsigned>(connInfo.getConnHandle()),
        static_cast<double>(connInfo.getConnInterval()) * 1.25,
        static_cast<double>(connInfo.getConnTimeout()) * 0.010,
        static_cast<unsigned>(g_bleMtu));
  }

  void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int reason) override {
    g_bleConnected = false;
    g_canSubscribed = false;
    g_gpsSubscribed = false;
    g_gpsTimeSubscribed = false;
    g_lastBleDisconnectReason = reason;
    g_lastBleDisconnectMs = millis();
    ++g_bleDisconnectCount;
    g_nextAdvertisingCheckMs = millis() + 1000;

    // Do not touch TWAI, the PID cache, GPS, or the advertiser here.
    // NimBLE's advertiseOnDisconnect handles the normal recovery path.
    Serial.printf("BLE: disconnected reason=%d; state retained\n", reason);
  }

  void onMTUChange(uint16_t mtu, NimBLEConnInfo&) override {
    g_bleMtu = mtu;
    Serial.printf("BLE: MTU=%u\n", static_cast<unsigned>(mtu));
  }
};

static ServerCallbacks g_serverCallbacks;

class SubscriptionCallbacks final : public NimBLECharacteristicCallbacks {
 public:
  explicit SubscriptionCallbacks(volatile bool* flag) : flag_(flag) {}

  void onSubscribe(NimBLECharacteristic*,
                   NimBLEConnInfo&,
                   uint16_t subscriptionValue) override {
    if (flag_ != nullptr) {
      *flag_ = subscriptionValue != 0;
    }
  }

  void onStatus(NimBLECharacteristic*, int code) override {
    // Notifications report zero on completion. Any non-zero status is treated
    // as backpressure; pause briefly instead of tearing down the connection.
    if (code == 0) return;
    ++g_bleNotifyFailures;
    g_lastBleNotifyFailureMs = millis();
    g_bleNotifyBackoffUntilMs = g_lastBleNotifyFailureMs + 100u;
  }

 private:
  volatile bool* flag_;
};

static SubscriptionCallbacks g_canSubscriptionCallbacks(&g_canSubscribed);
static SubscriptionCallbacks g_gpsSubscriptionCallbacks(&g_gpsSubscribed);
static SubscriptionCallbacks g_gpsTimeSubscriptionCallbacks(
    &g_gpsTimeSubscribed);

static void handleRaceChronoFilterWrite(const uint8_t* data, size_t length) {
  if (data == nullptr || length < 1) return;

  ++g_filterCommandCount;

  switch (data[0]) {
    case 0:  // Deny all.
      if (length != 1) return;
      memset(g_requestedPids, 0, sizeof(g_requestedPids));
      g_raceChronoFilterActive = true;
      g_raceChronoAllowAll = false;
      g_raceChronoAllowAllIntervalMs = 0;
      Serial.println("FIL: deny all");
      return;

    case 1:  // Allow all, interval is big-endian.
      if (length != 3) return;
      memset(g_requestedPids, 0, sizeof(g_requestedPids));
      g_raceChronoFilterActive = true;
      g_raceChronoAllowAll = true;
      g_raceChronoAllowAllIntervalMs =
          (static_cast<uint16_t>(data[1]) << 8) |
          static_cast<uint16_t>(data[2]);
      Serial.printf("FIL: allow all interval=%ums\n",
                    static_cast<unsigned>(g_raceChronoAllowAllIntervalMs));
      return;

    case 2: {  // Allow one PID; interval and PID are big-endian.
      if (length != 7) return;
      const uint16_t interval =
          (static_cast<uint16_t>(data[1]) << 8) |
          static_cast<uint16_t>(data[2]);
      const uint32_t pid =
          (static_cast<uint32_t>(data[3]) << 24) |
          (static_cast<uint32_t>(data[4]) << 16) |
          (static_cast<uint32_t>(data[5]) << 8) |
          static_cast<uint32_t>(data[6]);

      g_raceChronoFilterActive = true;
      g_raceChronoAllowAll = false;
      if (!requestPid(pid, interval)) {
        Serial.printf("WARN: FIL PID table full; dropped 0x%03lX\n",
                      static_cast<unsigned long>(pid));
      }
      return;
    }

    default:
      return;
  }
}

class FilterCallbacks final : public NimBLECharacteristicCallbacks {
 public:
  void onWrite(NimBLECharacteristic* characteristic,
               NimBLEConnInfo&) override {
    if (characteristic == nullptr) return;
    const std::string value = characteristic->getValue();
    handleRaceChronoFilterWrite(
        reinterpret_cast<const uint8_t*>(value.data()), value.size());
  }
};

static FilterCallbacks g_filterCallbacks;

static void initBle() {
  Serial.println("BLE: initializing stability profile");

  NimBLEDevice::init(DEVICE_NAME);

  // 3 dBm is ample inside a vehicle and materially reduces radio current peaks
  // compared with the previous maximum-power setting.
  NimBLEDevice::setPower(static_cast<int8_t>(3));

  // RaceChrono's documented DIY service does not require pairing. The previous
  // passkey/encrypted-filter layer caused iOS pairing churn and rejected the
  // standard 1/3/7-byte filter packets.
  NimBLEDevice::setSecurityAuth(false, false, false);
  NimBLEDevice::setSecurityIOCap(BLE_HS_IO_NO_INPUT_OUTPUT);
  if (NimBLEDevice::getNumBonds() > 0) {
    NimBLEDevice::deleteAllBonds();
    Serial.println("BLE: cleared obsolete bonds");
  }

  g_bleServer = NimBLEDevice::createServer();
  g_bleServer->setCallbacks(&g_serverCallbacks, false);
  g_bleServer->advertiseOnDisconnect(true);

  g_bleService = g_bleServer->createService(RC_SERVICE_UUID);

  g_canCharacteristic = g_bleService->createCharacteristic(
      RC_CHAR_CAN_UUID, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  g_filterCharacteristic = g_bleService->createCharacteristic(
      RC_CHAR_FILTER_UUID, NIMBLE_PROPERTY::WRITE);
  g_gpsCharacteristic = g_bleService->createCharacteristic(
      RC_CHAR_GPS_UUID, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  g_gpsTimeCharacteristic = g_bleService->createCharacteristic(
      RC_CHAR_GPS_TIME_UUID,
      NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);

  g_canCharacteristic->setCallbacks(&g_canSubscriptionCallbacks);
  g_filterCharacteristic->setCallbacks(&g_filterCallbacks);
  g_gpsCharacteristic->setCallbacks(&g_gpsSubscriptionCallbacks);
  g_gpsTimeCharacteristic->setCallbacks(
      &g_gpsTimeSubscriptionCallbacks);

  uint8_t initialCan[4] = {0, 0, 0, 0};
  uint8_t initialGps[20];
  memset(initialGps, 0xFF, sizeof(initialGps));
  uint8_t initialGpsTime[3] = {0, 0, 0};

  g_canCharacteristic->setValue(initialCan, sizeof(initialCan));
  g_gpsCharacteristic->setValue(initialGps, sizeof(initialGps));
  g_gpsTimeCharacteristic->setValue(initialGpsTime,
                                    sizeof(initialGpsTime));

  g_bleService->start();

  g_bleAdvertising = NimBLEDevice::getAdvertising();
  g_bleAdvertising->setName(DEVICE_NAME);
  g_bleAdvertising->setMinInterval(32);   // 20 ms
  g_bleAdvertising->setMaxInterval(160);  // 100 ms
  g_bleAdvertising->enableScanResponse(false);
  g_bleAdvertising->addServiceUUID(RC_SERVICE_UUID);

  g_nextAdvertisingCheckMs = 0;
  startAdvertisingIfNeeded(millis(), true);
}

// -----------------------------------------------------------------------------
// TWAI/CAN
// -----------------------------------------------------------------------------

static bool g_canDriverInstalled = false;
static bool g_canRunning = false;
static uint32_t g_canNextStartMs = 0;
static uint32_t g_canStartBackoffMs = 500;
static uint32_t g_canStartAttempts = 0;
static uint32_t g_canStartFailures = 0;
static uint32_t g_canRestartCount = 0;
static uint32_t g_canBusOffCount = 0;
static uint32_t g_canFaultCount = 0;
static uint32_t g_canRxCount = 0;
static uint32_t g_canExtendedCount = 0;
static uint32_t g_canRtrCount = 0;
static uint32_t g_canInvalidDlcCount = 0;
static uint32_t g_canRxQueueFullCount = 0;
static uint32_t g_canRxMissedCount = 0;
static uint32_t g_canSlotEvictions = 0;
static uint32_t g_lastCanFrameMs = 0;
static uint32_t g_lastCanHealthMs = 0;
static twai_status_info_t g_lastTwaiStatus = {};

static constexpr uint32_t TWAI_ALERTS =
    TWAI_ALERT_ERR_PASS |
    TWAI_ALERT_BUS_OFF |
    TWAI_ALERT_BUS_RECOVERED |
    TWAI_ALERT_RECOVERY_IN_PROGRESS |
    TWAI_ALERT_ABOVE_ERR_WARN |
    TWAI_ALERT_RX_QUEUE_FULL |
    TWAI_ALERT_TX_FAILED |
    TWAI_ALERT_ARB_LOST;

struct CanSlot {
  bool used;
  bool dirty;
  bool extended;
  uint32_t pid;
  uint8_t length;
  uint8_t data[8];
  uint8_t lastSentLength;
  uint8_t lastSentData[8];
  bool hasLastSent;
  uint32_t lastRxMs;
  uint32_t lastSentMs;
  uint32_t receiveCount;
};

static constexpr size_t CAN_SLOT_COUNT = 96;
static CanSlot g_canSlots[CAN_SLOT_COUNT] = {};
static size_t g_canForwardCursor = 0;

static CanSlot* findCanSlot(uint32_t pid, bool extended) {
  for (size_t i = 0; i < CAN_SLOT_COUNT; ++i) {
    if (g_canSlots[i].used && g_canSlots[i].pid == pid &&
        g_canSlots[i].extended == extended) {
      return &g_canSlots[i];
    }
  }
  return nullptr;
}

static CanSlot* acquireCanSlot(uint32_t pid,
                               bool extended,
                               uint32_t now) {
  if (CanSlot* existing = findCanSlot(pid, extended)) return existing;

  for (size_t i = 0; i < CAN_SLOT_COUNT; ++i) {
    if (g_canSlots[i].used) continue;
    memset(&g_canSlots[i], 0, sizeof(g_canSlots[i]));
    g_canSlots[i].used = true;
    g_canSlots[i].pid = pid;
    g_canSlots[i].extended = extended;
    g_canSlots[i].lastRxMs = now;
    return &g_canSlots[i];
  }

  // Preserve the newest bus state by replacing the least-recently-updated slot.
  size_t oldestIndex = 0;
  uint32_t oldestAge = 0;
  for (size_t i = 0; i < CAN_SLOT_COUNT; ++i) {
    const uint32_t age = now - g_canSlots[i].lastRxMs;
    if (age >= oldestAge) {
      oldestAge = age;
      oldestIndex = i;
    }
  }

  ++g_canSlotEvictions;
  memset(&g_canSlots[oldestIndex], 0, sizeof(g_canSlots[oldestIndex]));
  g_canSlots[oldestIndex].used = true;
  g_canSlots[oldestIndex].pid = pid;
  g_canSlots[oldestIndex].extended = extended;
  g_canSlots[oldestIndex].lastRxMs = now;
  return &g_canSlots[oldestIndex];
}

static void cacheCanFrame(uint32_t pid,
                          bool extended,
                          const uint8_t* data,
                          uint8_t length,
                          uint32_t now) {
  CanSlot* slot = acquireCanSlot(pid, extended, now);
  if (slot == nullptr) return;

  slot->length = length > 8 ? 8 : length;
  if (slot->length > 0 && data != nullptr) {
    memcpy(slot->data, data, slot->length);
  }
  if (slot->length < sizeof(slot->data)) {
    memset(slot->data + slot->length, 0,
           sizeof(slot->data) - slot->length);
  }

  slot->lastRxMs = now;
  slot->dirty = true;
  if (slot->receiveCount != 0xFFFFFFFFu) ++slot->receiveCount;
}

static void publishVirtualCan(uint32_t pid,
                              const uint8_t* data,
                              uint8_t length,
                              uint32_t now) {
  cacheCanFrame(pid, false, data, length, now);
}

static void stopCanDriver() {
  if (g_canDriverInstalled) {
    (void)twai_stop();
    (void)twai_driver_uninstall();
  }

  g_canDriverInstalled = false;
  g_canRunning = false;
  memset(&g_lastTwaiStatus, 0, sizeof(g_lastTwaiStatus));
  g_lastTwaiStatus.state = TWAI_STATE_STOPPED;
}

static void scheduleCanRestart(uint32_t now, const char* reason) {
  if (reason != nullptr) {
    Serial.printf("CAN: recovery scheduled (%s)\n", reason);
  }

  stopCanDriver();
  ++g_canFaultCount;
  g_canNextStartMs = now + g_canStartBackoffMs;

  if (g_canStartBackoffMs < 10000u) {
    g_canStartBackoffMs *= 2u;
    if (g_canStartBackoffMs > 10000u) g_canStartBackoffMs = 10000u;
  }
}

static bool startCanDriver(uint32_t now) {
  ++g_canStartAttempts;

  twai_general_config_t general = TWAI_GENERAL_CONFIG_DEFAULT(
      static_cast<gpio_num_t>(CAN_TX_GPIO),
      static_cast<gpio_num_t>(CAN_RX_GPIO),
      TWAI_MODE_NORMAL);
  general.tx_queue_len = 4;
  general.rx_queue_len = 128;
  general.alerts_enabled = TWAI_ALERTS;

  twai_timing_config_t timing = TWAI_TIMING_CONFIG_500KBITS();
  twai_filter_config_t filter = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  esp_err_t installResult =
      twai_driver_install(&general, &timing, &filter);

  if (installResult == ESP_ERR_INVALID_STATE) {
    // Clean up any stale driver state left by an interrupted recovery.
    (void)twai_stop();
    (void)twai_driver_uninstall();
    installResult = twai_driver_install(&general, &timing, &filter);
  }

  if (installResult != ESP_OK) {
    ++g_canStartFailures;
    g_canRunning = false;
    g_canDriverInstalled = false;
    g_canNextStartMs = now + g_canStartBackoffMs;
    Serial.printf("WARN: TWAI install failed: %d; retry in %lums\n",
                  static_cast<int>(installResult),
                  static_cast<unsigned long>(g_canStartBackoffMs));
    if (g_canStartBackoffMs < 10000u) {
      g_canStartBackoffMs *= 2u;
      if (g_canStartBackoffMs > 10000u) g_canStartBackoffMs = 10000u;
    }
    return false;
  }

  g_canDriverInstalled = true;

  const esp_err_t startResult = twai_start();
  if (startResult != ESP_OK) {
    ++g_canStartFailures;
    Serial.printf("WARN: TWAI start failed: %d\n",
                  static_cast<int>(startResult));
    stopCanDriver();
    g_canNextStartMs = now + g_canStartBackoffMs;
    return false;
  }

  g_canRunning = true;
  g_canStartBackoffMs = 500;
  g_canNextStartMs = 0;
  ++g_canRestartCount;
  g_lastCanHealthMs = now;
  memset(&g_lastTwaiStatus, 0, sizeof(g_lastTwaiStatus));
  g_lastTwaiStatus.state = TWAI_STATE_RUNNING;

  Serial.println("CAN: TWAI running, 500 kbit/s, accept-all");
  return true;
}

static void serviceCanStart(uint32_t now) {
  if (g_canRunning) return;
  if (!timeReached(now, g_canNextStartMs)) return;
  startCanDriver(now);
}

static void serviceCanHealth(uint32_t now) {
  if (!g_canRunning || !g_canDriverInstalled) return;
  if (now - g_lastCanHealthMs < 1000u) return;
  g_lastCanHealthMs = now;

  uint32_t alerts = 0;
  const esp_err_t alertResult =
      twai_read_alerts(&alerts, pdMS_TO_TICKS(0));
  if (alertResult != ESP_OK && alertResult != ESP_ERR_TIMEOUT) {
    Serial.printf("WARN: TWAI alert read failed: %d\n",
                  static_cast<int>(alertResult));
  }

  twai_status_info_t status = {};
  const esp_err_t statusResult = twai_get_status_info(&status);
  if (statusResult != ESP_OK) {
    scheduleCanRestart(now, "status read failed");
    return;
  }

  g_lastTwaiStatus = status;
  g_canRxMissedCount = status.rx_missed_count;

  if ((alerts & TWAI_ALERT_RX_QUEUE_FULL) != 0) {
    ++g_canRxQueueFullCount;
  }

  if (status.state == TWAI_STATE_BUS_OFF ||
      (alerts & TWAI_ALERT_BUS_OFF) != 0) {
    ++g_canBusOffCount;
    scheduleCanRestart(now, "bus off");
    return;
  }

  if (status.state == TWAI_STATE_STOPPED) {
    scheduleCanRestart(now, "controller stopped");
    return;
  }

  // CAN silence is not a fault. The bench generator may stop and the vehicle
  // may enter quiet states; no timeout-based controller reset is performed.
}

static void serviceCanReceive(uint32_t now) {
  if (!g_canRunning) return;

  const uint32_t startUs = micros();
  uint16_t framesThisPass = 0;

  while (framesThisPass < 96 &&
         static_cast<uint32_t>(micros() - startUs) < 2000u) {
    twai_message_t frame = {};
    if (twai_receive(&frame, pdMS_TO_TICKS(0)) != ESP_OK) break;

    ++framesThisPass;
    if (frame.rtr) {
      ++g_canRtrCount;
      continue;
    }

    if (frame.data_length_code > 8) {
      ++g_canInvalidDlcCount;
      continue;
    }

    ++g_canRxCount;
    if (frame.extd) ++g_canExtendedCount;
    g_lastCanFrameMs = now;

    cacheCanFrame(frame.identifier, frame.extd != 0, frame.data,
                  frame.data_length_code, now);
  }
}

static bool sendCanSlot(CanSlot& slot, uint32_t now) {
  uint8_t packet[12] = {};
  packet[0] = static_cast<uint8_t>(slot.pid & 0xFFu);
  packet[1] = static_cast<uint8_t>((slot.pid >> 8) & 0xFFu);
  packet[2] = static_cast<uint8_t>((slot.pid >> 16) & 0xFFu);
  packet[3] = static_cast<uint8_t>((slot.pid >> 24) & 0xFFu);
  if (slot.length > 0) {
    memcpy(packet + 4, slot.data, slot.length);
  }

  if (!notifyCharacteristic(g_canCharacteristic, g_canSubscribed,
                            packet, 4u + slot.length, now)) {
    return false;
  }

  slot.lastSentLength = slot.length;
  memcpy(slot.lastSentData, slot.data, sizeof(slot.lastSentData));
  slot.hasLastSent = true;
  slot.lastSentMs = now;
  slot.dirty = false;
  slot.receiveCount = 0;
  return true;
}

static void serviceCanForwarding(uint32_t now) {
  if (!isBleConnected() || !g_canSubscribed) return;
  if (!timeReached(now, g_bleNotifyBackoffUntilMs)) return;

  uint8_t sentThisPass = 0;

  for (size_t checked = 0;
       checked < CAN_SLOT_COUNT && sentThisPass < 4;
       ++checked) {
    const size_t index = g_canForwardCursor % CAN_SLOT_COUNT;
    g_canForwardCursor = (g_canForwardCursor + 1) % CAN_SLOT_COUNT;

    CanSlot& slot = g_canSlots[index];
    if (!slot.used || !slot.dirty) continue;

    const RouteDecision decision = routeDecision(slot.pid);
    if (!decision.allowed) {
      slot.dirty = false;
      slot.receiveCount = 0;
      continue;
    }

    if (slot.hasLastSent &&
        now - slot.lastSentMs < decision.minimumIntervalMs) {
      continue;
    }

    if (sendCanSlot(slot, now)) {
      ++sentThisPass;
    } else {
      // Keep the latest value dirty for a later pass; do not spin.
      break;
    }
  }
}

// -----------------------------------------------------------------------------
// GPS
// -----------------------------------------------------------------------------

static HardwareSerial g_gpsSerial(1);

static constexpr uint32_t MILLIS_PER_SECOND = 1000u;
static constexpr uint32_t MILLIS_PER_MINUTE = 60u * MILLIS_PER_SECOND;
static constexpr uint32_t MILLIS_PER_HOUR = 60u * MILLIS_PER_MINUTE;
static constexpr uint32_t MILLIS_PER_DAY = 24u * MILLIS_PER_HOUR;
static constexpr int64_t MICROS_PER_DAY =
    static_cast<int64_t>(MILLIS_PER_DAY) * 1000LL;

static constexpr const char* PMTK_RMC_GGA_ONLY =
    "$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n";
static constexpr const char* PMTK_10HZ =
    "$PMTK220,100*2F\r\n";
static constexpr const char* PMTK_115200 =
    "$PMTK251,115200*1F\r\n";

enum class GpsState : uint8_t {
  Probe,
  Configure,
  SwitchTo115200,
  Active,
  RetryWait,
};

static constexpr uint32_t GPS_PROBE_BAUDS[] = {
    115200, 9600, 38400, 57600
};
static constexpr size_t GPS_PROBE_BAUD_COUNT =
    sizeof(GPS_PROBE_BAUDS) / sizeof(GPS_PROBE_BAUDS[0]);

static GpsState g_gpsState = GpsState::Probe;
static size_t g_gpsProbeIndex = 0;
static uint32_t g_gpsCurrentBaud = 115200;
static uint32_t g_gpsStateDeadlineMs = 0;
static uint8_t g_gpsConfigCommandIndex = 0;
static bool g_gpsSentenceSeenAtCurrentBaud = false;
static bool g_gpsConfigured = false;
static bool g_gpsValidFix = false;
static uint32_t g_gpsSentenceCount = 0;
static uint32_t g_gpsParseFailureCount = 0;
static uint32_t g_gpsLastSentenceMs = 0;
static uint32_t g_gpsLastValidFixMs = 0;
static uint32_t g_gpsLastNotifyMs = 0;
static uint32_t g_gpsLastTimeNotifyMs = 0;

static char g_gpsLine[160] = {};
static size_t g_gpsLineLength = 0;

static int g_rmcHour = 0;
static int g_rmcMinute = 0;
static int g_rmcSecond = 0;
static int g_rmcMillis = 0;
static double g_rmcLatitudeDeg = 0.0;
static double g_rmcLongitudeDeg = 0.0;
static double g_rmcSpeedKmh = 0.0;
static double g_rmcCourseDeg = 0.0;

static int g_gpsYear = 2000;
static int g_gpsMonth = 1;
static int g_gpsDay = 1;
static int g_ggaSatellites = 0;
static double g_ggaHdop = 99.9;
static double g_ggaAltitudeMeters = 0.0;

static bool g_rmcTimeAvailable = false;
static uint32_t g_rmcMillisSinceMidnight = 0;
static uint32_t g_rmcCaptureMillis = 0;
static uint32_t g_rmcCaptureMicros = 0;
static int64_t g_gpsTimeCorrectionMicros = 0;
static uint32_t g_gpsMonotonicMillis = 0;
static uint8_t g_gpsSyncBits = 0;
static int g_lastDateHourPacked = -1;

#if GPS_PPS_GPIO >= 0
static volatile uint32_t g_ppsEventMicros = 0;
static volatile uint32_t g_ppsLastIsrMicros = 0;
static volatile uint32_t g_ppsIntervalMicros = 0;
static volatile uint32_t g_ppsPendingCount = 0;
static uint32_t g_ppsProcessedCount = 0;
static uint32_t g_ppsLastProcessedMs = 0;
static bool g_ppsLocked = false;

static void IRAM_ATTR onGpsPps() {
  const uint32_t now = micros();
  const uint32_t last = g_ppsLastIsrMicros;
  if (last != 0 && static_cast<uint32_t>(now - last) < 200000u) return;

  g_ppsLastIsrMicros = now;
  g_ppsEventMicros = now;
  g_ppsIntervalMicros = last == 0 ? 1000000u
                                  : static_cast<uint32_t>(now - last);
  if (g_ppsPendingCount != 0xFFFFFFFFu) ++g_ppsPendingCount;
}
#endif

static uint32_t millisSinceMidnight(int hour,
                                    int minute,
                                    int second,
                                    int millisPart) {
  uint64_t total =
      static_cast<uint64_t>(hour < 0 ? 0 : hour) * MILLIS_PER_HOUR +
      static_cast<uint64_t>(minute < 0 ? 0 : minute) *
          MILLIS_PER_MINUTE +
      static_cast<uint64_t>(second < 0 ? 0 : second) *
          MILLIS_PER_SECOND +
      static_cast<uint64_t>(millisPart < 0 ? 0 : millisPart);
  return static_cast<uint32_t>(total % MILLIS_PER_DAY);
}

static int64_t correctedGpsMicros(uint32_t nowMicros) {
  if (!g_rmcTimeAvailable) {
    return static_cast<int64_t>(g_gpsMonotonicMillis) * 1000LL;
  }

  const uint32_t delta = nowMicros - g_rmcCaptureMicros;
  int64_t candidate =
      static_cast<int64_t>(g_rmcMillisSinceMidnight) * 1000LL +
      static_cast<int64_t>(delta) +
      g_gpsTimeCorrectionMicros;

  candidate %= MICROS_PER_DAY;
  if (candidate < 0) candidate += MICROS_PER_DAY;
  return candidate;
}

static uint32_t gpsMillisNow() {
  if (!g_rmcTimeAvailable) return g_gpsMonotonicMillis;

  uint32_t candidate =
      static_cast<uint32_t>(correctedGpsMicros(micros()) / 1000LL);

  if (candidate < g_gpsMonotonicMillis) {
    const uint32_t backwards = g_gpsMonotonicMillis - candidate;
    if (backwards < 2000u ||
        backwards < (MILLIS_PER_DAY - 2000u)) {
      candidate = g_gpsMonotonicMillis;
    }
  }

  g_gpsMonotonicMillis = candidate;
  return candidate;
}

static void servicePps(uint32_t now) {
#if GPS_PPS_GPIO >= 0
  uint32_t eventMicros = 0;
  uint32_t pending = 0;

  noInterrupts();
  pending = g_ppsPendingCount;
  if (pending > 0) {
    g_ppsPendingCount = 0;
    eventMicros = g_ppsEventMicros;
  }
  interrupts();

  if (pending > 0) {
    g_ppsProcessedCount += pending;
    g_ppsLastProcessedMs = now;

    if (g_rmcTimeAvailable) {
      const int64_t candidate = correctedGpsMicros(eventMicros);
      int64_t nearestSecond =
          ((candidate + 500000LL) / 1000000LL) * 1000000LL;
      if (nearestSecond >= MICROS_PER_DAY) {
        nearestSecond -= MICROS_PER_DAY;
      }

      int64_t error = nearestSecond - candidate;
      if (error > MICROS_PER_DAY / 2) error -= MICROS_PER_DAY;
      if (error < -MICROS_PER_DAY / 2) error += MICROS_PER_DAY;

      if (error > 2000LL) error = 2000LL;
      if (error < -2000LL) error = -2000LL;

      g_gpsTimeCorrectionMicros += error;
      g_ppsLocked = true;
    }
  }

  if (g_ppsLocked && now - g_ppsLastProcessedMs > 2500u) {
    g_ppsLocked = false;
  }
#else
  (void)now;
#endif
}

static void startGpsProbe(size_t index, uint32_t now) {
  if (index >= GPS_PROBE_BAUD_COUNT) index = 0;

  g_gpsProbeIndex = index;
  g_gpsCurrentBaud = GPS_PROBE_BAUDS[index];
  g_gpsSentenceSeenAtCurrentBaud = false;
  g_gpsLineLength = 0;
  g_gpsSerial.end();
  g_gpsSerial.begin(g_gpsCurrentBaud, SERIAL_8N1,
                    GPS_RX_GPIO, GPS_TX_GPIO);
  g_gpsState = GpsState::Probe;
  g_gpsStateDeadlineMs = now + 1500u;

  Serial.printf("GPS: probing %lu baud\n",
                static_cast<unsigned long>(g_gpsCurrentBaud));
}

static void enterGpsRetryWait(uint32_t now) {
  g_gpsValidFix = false;
  g_gpsState = GpsState::RetryWait;
  g_gpsStateDeadlineMs = now + 60000u;
  g_gpsConfigured = false;
  Serial.println("GPS: no stream; next probe in 60s");
}

static void parseGpsSentence(const char* line, uint32_t now) {
  if (line == nullptr || line[0] != '$') return;

  char work[sizeof(g_gpsLine)];
  strncpy(work, line, sizeof(work) - 1);
  work[sizeof(work) - 1] = '\0';

  bool parsed = false;

  if (strstr(work, "GPRMC") != nullptr ||
      strstr(work, "GNRMC") != nullptr) {
    gps::RmcData rmc;
    if (gps::parseRmcSentence(work, rmc)) {
      parsed = true;

      if (rmc.has_time) {
        g_rmcHour = rmc.hour;
        g_rmcMinute = rmc.minute;
        g_rmcSecond = rmc.second;
        g_rmcMillis = rmc.millis;
        g_rmcMillisSinceMidnight = millisSinceMidnight(
            g_rmcHour, g_rmcMinute, g_rmcSecond, g_rmcMillis);
        g_rmcCaptureMillis = now;
        g_rmcCaptureMicros = micros();
        if (!g_rmcTimeAvailable) {
          g_gpsMonotonicMillis = g_rmcMillisSinceMidnight;
        }
        g_rmcTimeAvailable = true;
      }

      g_gpsValidFix = rmc.valid;
      if (rmc.valid) g_gpsLastValidFixMs = now;
      if (rmc.has_latitude) g_rmcLatitudeDeg = rmc.latitude_deg;
      if (rmc.has_longitude) g_rmcLongitudeDeg = rmc.longitude_deg;
      g_rmcSpeedKmh = rmc.speed_kmh;
      g_rmcCourseDeg = rmc.course_deg;

      if (rmc.has_date) {
        g_gpsDay = rmc.day;
        g_gpsMonth = rmc.month;
        g_gpsYear = rmc.year;
      }
    }
  } else if (strstr(work, "GPGGA") != nullptr ||
             strstr(work, "GNGGA") != nullptr) {
    gps::GgaData gga;
    if (gps::parseGgaSentence(work, gga)) {
      parsed = true;
      g_ggaSatellites = gga.has_sats ? gga.sats : 0;
      g_ggaHdop = gga.has_hdop ? gga.hdop : 99.9;
      g_ggaAltitudeMeters =
          gga.has_altitude ? gga.altitude_m : 0.0;
    }
  }

  if (!parsed) {
    ++g_gpsParseFailureCount;
    return;
  }

  ++g_gpsSentenceCount;
  g_gpsLastSentenceMs = now;
  g_gpsSentenceSeenAtCurrentBaud = true;

  if (g_gpsState == GpsState::Probe) {
    if (g_gpsCurrentBaud == 115200u) {
      g_gpsState = GpsState::Active;
      g_gpsConfigured = true;
      Serial.println("GPS: active at 115200");
    } else {
      g_gpsState = GpsState::Configure;
      g_gpsConfigCommandIndex = 0;
      g_gpsStateDeadlineMs = now;
      Serial.printf("GPS: stream found at %lu; configuring 10Hz/115200\n",
                    static_cast<unsigned long>(g_gpsCurrentBaud));
    }
  }
}

static void readGpsBytes(uint32_t now) {
  size_t processed = 0;

  while (g_gpsSerial.available() && processed < 512u) {
    ++processed;
    const int raw = g_gpsSerial.read();
    if (raw < 0) break;

    const char c = static_cast<char>(raw);
    if (c == '\r') continue;

    if (c == '\n') {
      if (g_gpsLineLength > 0) {
        g_gpsLine[g_gpsLineLength] = '\0';
        parseGpsSentence(g_gpsLine, now);
      }
      g_gpsLineLength = 0;
      continue;
    }

    if (g_gpsLineLength < sizeof(g_gpsLine) - 1) {
      g_gpsLine[g_gpsLineLength++] = c;
    } else {
      g_gpsLineLength = 0;
    }
  }
}

static void serviceGpsStateMachine(uint32_t now) {
  switch (g_gpsState) {
    case GpsState::Probe:
      if (g_gpsSentenceSeenAtCurrentBaud) return;
      if (!timeReached(now, g_gpsStateDeadlineMs)) return;

      if (g_gpsProbeIndex + 1 < GPS_PROBE_BAUD_COUNT) {
        startGpsProbe(g_gpsProbeIndex + 1, now);
      } else {
        enterGpsRetryWait(now);
      }
      return;

    case GpsState::Configure: {
      if (!timeReached(now, g_gpsStateDeadlineMs)) return;

      static constexpr const char* commands[] = {
          PMTK_RMC_GGA_ONLY, PMTK_10HZ, PMTK_115200
      };

      if (g_gpsConfigCommandIndex <
          sizeof(commands) / sizeof(commands[0])) {
        g_gpsSerial.print(commands[g_gpsConfigCommandIndex]);
        ++g_gpsConfigCommandIndex;
        g_gpsStateDeadlineMs = now + 150u;
      } else {
        g_gpsState = GpsState::SwitchTo115200;
        g_gpsStateDeadlineMs = now + 250u;
      }
      return;
    }

    case GpsState::SwitchTo115200:
      if (!timeReached(now, g_gpsStateDeadlineMs)) return;
      startGpsProbe(0, now);
      return;

    case GpsState::Active:
      if (g_gpsLastSentenceMs != 0 &&
          now - g_gpsLastSentenceMs > 5000u) {
        g_gpsConfigured = false;
        g_gpsValidFix = false;
        g_gpsState = GpsState::RetryWait;
        g_gpsStateDeadlineMs = now + 10000u;
        Serial.println("GPS: stream stale; reprobe scheduled");
      }
      return;

    case GpsState::RetryWait:
      if (timeReached(now, g_gpsStateDeadlineMs)) {
        startGpsProbe(0, now);
      }
      return;
  }
}

static int clampInt(int value, int low, int high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

static void serviceGpsNotifications(uint32_t now) {
  if (!isBleConnected()) return;

  if (g_gpsSubscribed && now - g_gpsLastNotifyMs >= 100u) {
    g_gpsLastNotifyMs = now;

    uint8_t payload[20];
    memset(payload, 0xFF, sizeof(payload));

    const uint32_t utcMillis = gpsMillisNow();
    const uint32_t millisIntoHour = utcMillis % MILLIS_PER_HOUR;
    const int hour =
        static_cast<int>((utcMillis / MILLIS_PER_HOUR) % 24u);

    const int year = g_gpsYear >= 2000 ? g_gpsYear : 2000;
    const int month =
        (g_gpsMonth >= 1 && g_gpsMonth <= 12) ? g_gpsMonth : 1;
    const int day =
        (g_gpsDay >= 1 && g_gpsDay <= 31) ? g_gpsDay : 1;

    const int dateHour =
        ((year - 2000) * 8928) +
        ((month - 1) * 744) +
        ((day - 1) * 24) +
        hour;

    if (dateHour != g_lastDateHourPacked) {
      g_lastDateHourPacked = dateHour;
      g_gpsSyncBits = static_cast<uint8_t>((g_gpsSyncBits + 1) & 0x7);
    }

    const int timeSinceHour =
        static_cast<int>(millisIntoHour / 2u);
    const uint8_t fixQuality = g_gpsValidFix ? 1 : 0;
    const uint8_t satellites =
        static_cast<uint8_t>(clampInt(g_ggaSatellites, 0, 63));

    const int32_t latitude =
        static_cast<int32_t>(lround(g_rmcLatitudeDeg * 10000000.0));
    const int32_t longitude =
        static_cast<int32_t>(lround(g_rmcLongitudeDeg * 10000000.0));

    int altitudeWord = 0xFFFF;
    if (g_ggaAltitudeMeters > -7000.0 &&
        g_ggaAltitudeMeters < 20000.0) {
      if (g_ggaAltitudeMeters >= -500.0 &&
          g_ggaAltitudeMeters <= 6053.5) {
        altitudeWord = clampInt(
            static_cast<int>(
                lround((g_ggaAltitudeMeters + 500.0) * 10.0)),
            0, 0x7FFF);
      } else {
        altitudeWord =
            (static_cast<int>(lround(g_ggaAltitudeMeters + 500.0)) &
             0x7FFF) |
            0x8000;
      }
    }

    int speedWord = 0xFFFF;
    if (g_rmcSpeedKmh >= 0.0 && g_rmcSpeedKmh <= 655.35) {
      speedWord = clampInt(
          static_cast<int>(lround(g_rmcSpeedKmh * 100.0)),
          0, 0x7FFF);
    } else if (g_rmcSpeedKmh > 655.35) {
      speedWord =
          (static_cast<int>(lround(g_rmcSpeedKmh * 10.0)) &
           0x7FFF) |
          0x8000;
    }

    const int bearing = clampInt(
        static_cast<int>(lround(g_rmcCourseDeg * 100.0)),
        0, 0xFFFF);
    const uint8_t hdop =
        (g_ggaHdop >= 0.0 && g_ggaHdop <= 25.4)
            ? static_cast<uint8_t>(lround(g_ggaHdop * 10.0))
            : 0xFF;

    payload[0] = static_cast<uint8_t>(
        ((g_gpsSyncBits & 0x7) << 5) |
        ((timeSinceHour >> 16) & 0x1F));
    payload[1] = static_cast<uint8_t>(timeSinceHour >> 8);
    payload[2] = static_cast<uint8_t>(timeSinceHour);
    payload[3] = static_cast<uint8_t>(
        ((fixQuality & 0x3) << 6) | (satellites & 0x3F));

    payload[4] = static_cast<uint8_t>(latitude >> 24);
    payload[5] = static_cast<uint8_t>(latitude >> 16);
    payload[6] = static_cast<uint8_t>(latitude >> 8);
    payload[7] = static_cast<uint8_t>(latitude);

    payload[8] = static_cast<uint8_t>(longitude >> 24);
    payload[9] = static_cast<uint8_t>(longitude >> 16);
    payload[10] = static_cast<uint8_t>(longitude >> 8);
    payload[11] = static_cast<uint8_t>(longitude);

    payload[12] = static_cast<uint8_t>(altitudeWord >> 8);
    payload[13] = static_cast<uint8_t>(altitudeWord);
    payload[14] = static_cast<uint8_t>(speedWord >> 8);
    payload[15] = static_cast<uint8_t>(speedWord);
    payload[16] = static_cast<uint8_t>(bearing >> 8);
    payload[17] = static_cast<uint8_t>(bearing);
    payload[18] = hdop;
    payload[19] = 0xFF;  // VDOP unavailable from RMC/GGA.

    notifyCharacteristic(g_gpsCharacteristic, g_gpsSubscribed,
                         payload, sizeof(payload), now);
  }

  // Date/hour changes very slowly; 1 Hz is sufficient and avoids needless
  // BLE load. RaceChrono still receives the 10 Hz fine time in 0x0003.
  if (g_gpsTimeSubscribed &&
      now - g_gpsLastTimeNotifyMs >= 1000u) {
    g_gpsLastTimeNotifyMs = now;

    const uint32_t utcMillis = gpsMillisNow();
    const int hour =
        static_cast<int>((utcMillis / MILLIS_PER_HOUR) % 24u);
    const int year = g_gpsYear >= 2000 ? g_gpsYear : 2000;
    const int month =
        (g_gpsMonth >= 1 && g_gpsMonth <= 12) ? g_gpsMonth : 1;
    const int day =
        (g_gpsDay >= 1 && g_gpsDay <= 31) ? g_gpsDay : 1;
    const int dateHour =
        ((year - 2000) * 8928) +
        ((month - 1) * 744) +
        ((day - 1) * 24) +
        hour;

    uint8_t payload[3];
    payload[0] = static_cast<uint8_t>(
        ((g_gpsSyncBits & 0x7) << 5) |
        ((dateHour >> 16) & 0x1F));
    payload[1] = static_cast<uint8_t>(dateHour >> 8);
    payload[2] = static_cast<uint8_t>(dateHour);

    notifyCharacteristic(g_gpsTimeCharacteristic,
                         g_gpsTimeSubscribed,
                         payload, sizeof(payload), now);
  }
}

static void serviceGps(uint32_t now) {
  readGpsBytes(now);
  serviceGpsStateMachine(now);
  servicePps(now);
  serviceGpsNotifications(now);
}

// -----------------------------------------------------------------------------
// Oil pressure ADC / virtual CAN 0x710
// -----------------------------------------------------------------------------

static constexpr float OIL_PRESSURE_MIN_PSI = 0.0f;
static constexpr float OIL_PRESSURE_MAX_PSI = 150.0f;
static constexpr float DEFAULT_OIL_V0_ADC = 0.3482f;
static constexpr float DEFAULT_OIL_V1_ADC = 3.1290f;
static constexpr float ADC_VALID_MAX_VOLTS = 3.60f;
static constexpr float ADC_IIR_ALPHA = 0.15f;
static constexpr float ADC_DEADBAND_PSI = 0.5f;

static float g_oilV0Adc = DEFAULT_OIL_V0_ADC;
static float g_oilV1Adc = DEFAULT_OIL_V1_ADC;
static float g_oilFilteredVolts = DEFAULT_OIL_V0_ADC;
static float g_oilPsi = 0.0f;
static uint8_t g_oilFlags = 0;
static bool g_oilHaveValidSample = false;
static uint32_t g_lastOilSampleMs = 0;
static uint32_t g_lastOilPublishMs = 0;

static float readOilFilteredVolts() {
  float samples[5];

  for (size_t i = 0; i < 5; ++i) {
#if defined(ESP_ARDUINO_VERSION_MAJOR) && \
    (ESP_ARDUINO_VERSION_MAJOR >= 3)
    samples[i] =
        static_cast<float>(analogReadMilliVolts(OIL_ADC_PIN)) / 1000.0f;
#else
    uint32_t accumulator = 0;
    for (size_t sample = 0; sample < 8; ++sample) {
      accumulator += analogRead(OIL_ADC_PIN);
    }
    samples[i] =
        (static_cast<float>(accumulator) / (8.0f * 4095.0f)) * 3.30f;
#endif
  }

  for (size_t i = 1; i < 5; ++i) {
    const float value = samples[i];
    int j = static_cast<int>(i) - 1;
    while (j >= 0 && samples[j] > value) {
      samples[j + 1] = samples[j];
      --j;
    }
    samples[j + 1] = value;
  }

  const float median = samples[2];
  if (!isfinite(median) || median < 0.0f ||
      median > ADC_VALID_MAX_VOLTS) {
    return g_oilFilteredVolts;
  }

  if (!g_oilHaveValidSample) {
    g_oilFilteredVolts = median;
    g_oilHaveValidSample = true;
  } else {
    g_oilFilteredVolts =
        (1.0f - ADC_IIR_ALPHA) * g_oilFilteredVolts +
        ADC_IIR_ALPHA * median;
  }

  return g_oilFilteredVolts;
}

static uint8_t oilFlagsForVoltage(float volts) {
  uint8_t flags = 0;
  if (volts > g_oilV1Adc + 0.10f) flags |= (1u << 0);  // Open.
  if (volts < 0.05f) flags |= (1u << 1);               // Short.
  if (volts < g_oilV0Adc - 0.08f ||
      volts > g_oilV1Adc + 0.08f) {
    flags |= (1u << 2);  // Out of calibrated range.
  }
  return flags;
}

static float oilPsiForVoltage(float volts) {
  if (volts <= g_oilV0Adc + 0.020f) return OIL_PRESSURE_MIN_PSI;
  if (volts >= g_oilV1Adc - 0.010f) return OIL_PRESSURE_MAX_PSI;

  const float span = g_oilV1Adc - g_oilV0Adc;
  if (span <= 0.001f) return 0.0f;

  float psi =
      OIL_PRESSURE_MIN_PSI +
      ((volts - g_oilV0Adc) / span) *
          (OIL_PRESSURE_MAX_PSI - OIL_PRESSURE_MIN_PSI);
  psi = clampFloat(psi, OIL_PRESSURE_MIN_PSI,
                   OIL_PRESSURE_MAX_PSI);

  if (psi < OIL_PRESSURE_MIN_PSI + ADC_DEADBAND_PSI) {
    psi = OIL_PRESSURE_MIN_PSI;
  }
  if (psi > OIL_PRESSURE_MAX_PSI - ADC_DEADBAND_PSI) {
    psi = OIL_PRESSURE_MAX_PSI;
  }
  return psi;
}

static void loadOilCalibration() {
  if (!oil_calibration_load(&g_oilV0Adc, &g_oilV1Adc)) {
    g_oilV0Adc = DEFAULT_OIL_V0_ADC;
    g_oilV1Adc = DEFAULT_OIL_V1_ADC;
  }
}

static void serviceOil(uint32_t now) {
  if (now - g_lastOilSampleMs >= 20u) {
    g_lastOilSampleMs = now;
    const float volts = readOilFilteredVolts();
    g_oilFlags = oilFlagsForVoltage(volts);
    g_oilPsi = oilPsiForVoltage(volts);
  }

  if (now - g_lastOilPublishMs >= g_oilPublishPeriodMs) {
    g_lastOilPublishMs = now;

    const uint16_t pressureTenths = static_cast<uint16_t>(
        clampFloat(g_oilPsi * 10.0f, 0.0f, 1500.0f) + 0.5f);

    uint8_t payload[8] = {
        static_cast<uint8_t>(pressureTenths >> 8),
        static_cast<uint8_t>(pressureTenths & 0xFFu),
        g_oilFlags,
        0, 0, 0, 0, 0
    };

    publishVirtualCan(0x710u, payload, sizeof(payload), now);
  }
}

// -----------------------------------------------------------------------------
// Low-rate diagnostics virtual CAN frame
// -----------------------------------------------------------------------------

static uint32_t g_lastDiagnosticPublishMs = 0;

static void publishDiagnostics(uint32_t now) {
  if (now - g_lastDiagnosticPublishMs < 2000u) return;
  g_lastDiagnosticPublishMs = now;

  twai_status_info_t status = g_lastTwaiStatus;
  if (g_canRunning) {
    twai_status_info_t fresh = {};
    if (twai_get_status_info(&fresh) == ESP_OK) {
      status = fresh;
      g_lastTwaiStatus = fresh;
    }
  }

  const uint32_t freeHeap =
      heap_caps_get_free_size(MALLOC_CAP_8BIT);
  uint8_t heapKiB =
      static_cast<uint8_t>((freeHeap / 1024u) > 255u
                               ? 255u
                               : (freeHeap / 1024u));

  uint8_t payload[8] = {
      static_cast<uint8_t>(
          (2u << 4) |
          (g_canRunning
               ? (static_cast<uint8_t>(status.state) & 0x0Fu)
               : 0u)),
      static_cast<uint8_t>(status.tx_error_counter & 0xFFu),
      static_cast<uint8_t>(status.rx_error_counter & 0xFFu),
      static_cast<uint8_t>(status.rx_missed_count & 0xFFu),
      static_cast<uint8_t>(g_bleNotifyFailures & 0xFFu),
      static_cast<uint8_t>(g_canRestartCount & 0xFFu),
      heapKiB,
      static_cast<uint8_t>(g_bootResetReason)
  };

  publishVirtualCan(0x777u, payload, sizeof(payload), now);
}

// -----------------------------------------------------------------------------
// LED status
// -----------------------------------------------------------------------------

static uint32_t g_lastLedServiceMs = 0;

static void serviceStatusLeds(uint32_t now) {
  if (now - g_lastLedServiceMs < 20u) return;
  g_lastLedServiceMs = now;

  // Power is deliberately never changed after setup. If this LED physically
  // dims while Board3v3 and EN also droop, that is an electrical problem.
  led_set_power(LedPattern::Solid);

  led_set_ble(isBleConnected() ? LedPattern::Solid
                               : LedPattern::BlinkFast);

  if (!g_canRunning) {
    led_set_can(LedPattern::BlinkFast);
  } else if (g_lastCanFrameMs != 0 &&
             now - g_lastCanFrameMs <= 1000u) {
    led_set_can(LedPattern::Pulse2Every2s);
  } else {
    led_set_can(LedPattern::BlinkSlow);
  }

  if (g_gpsLastSentenceMs != 0 &&
      now - g_gpsLastSentenceMs <= 1500u) {
    led_set_gps(g_gpsValidFix ? LedPattern::Pulse3Every2s
                              : LedPattern::Solid);
  } else {
    led_set_gps(LedPattern::BlinkSlow);
  }

  const bool systemFault =
      (!g_canRunning && g_canStartFailures > 0) ||
      (g_lastBleNotifyFailureMs != 0 &&
       now - g_lastBleNotifyFailureMs < 2000u);
  led_set_sys(systemFault ? LedPattern::BlinkSlow
                          : LedPattern::Off);

  if (g_oilFlags == 0) {
    led_set_oil(LedPattern::Solid);
  } else if ((g_oilFlags & (1u << 1)) != 0) {
    led_set_oil(LedPattern::BlinkFast);
  } else if ((g_oilFlags & (1u << 0)) != 0) {
    led_set_oil(LedPattern::Pulse2Every2s);
  } else {
    led_set_oil(LedPattern::BlinkSlow);
  }

  led_service(now);
}

// -----------------------------------------------------------------------------
// Serial CLI
// -----------------------------------------------------------------------------

static void showConfig() {
  Serial.println("=== CCA Config ===");
  Serial.printf("Build:          %s\n", BUILD_ID);
  Serial.printf("Device:         %s\n", DEVICE_NAME);
  Serial.printf("Profile:        %s\n",
                g_profileEnabled ? "GR86 allow-list" : "sniff-all");
  Serial.printf("Oil V0/V1:      %.4f / %.4f V\n",
                g_oilV0Adc, g_oilV1Adc);
  Serial.printf("Oil rate:       %u ms\n",
                static_cast<unsigned>(g_oilPublishPeriodMs));
  Serial.printf("Custom divs:    %u\n",
                static_cast<unsigned>(g_customDividerCount));
  Serial.println("==================");
}

static void showStats() {
  const uint32_t now = millis();
  Serial.println("=== CCA Stats ===");
  Serial.printf("Uptime:         %lu ms\n",
                static_cast<unsigned long>(now));
  Serial.printf("Boot reason:    %s (%d)\n",
                resetReasonName(g_bootResetReason),
                static_cast<int>(g_bootResetReason));

  Serial.printf(
      "BLE: connected=%s can_sub=%s gps_sub=%s time_sub=%s mtu=%u\n",
      isBleConnected() ? "yes" : "no",
      g_canSubscribed ? "yes" : "no",
      g_gpsSubscribed ? "yes" : "no",
      g_gpsTimeSubscribed ? "yes" : "no",
      static_cast<unsigned>(g_bleMtu));
  Serial.printf(
      "BLE events: connect=%lu disconnect=%lu last_reason=%d adv=%lu/%lu\n",
      static_cast<unsigned long>(g_bleConnectCount),
      static_cast<unsigned long>(g_bleDisconnectCount),
      g_lastBleDisconnectReason,
      static_cast<unsigned long>(g_advertisingStartCount),
      static_cast<unsigned long>(g_advertisingStartFailures));
  Serial.printf(
      "BLE notify: ok=%lu fail=%lu rate_drop=%lu unsub_drop=%lu\n",
      static_cast<unsigned long>(g_bleNotifySuccesses),
      static_cast<unsigned long>(g_bleNotifyFailures),
      static_cast<unsigned long>(g_bleNotifyRateDrops),
      static_cast<unsigned long>(g_bleNotifyUnsubscribedDrops));
  Serial.printf(
      "FIL: active=%s allow_all=%s requested=%u commands=%lu\n",
      g_raceChronoFilterActive ? "yes" : "no",
      g_raceChronoAllowAll ? "yes" : "no",
      static_cast<unsigned>(requestedPidCount()),
      static_cast<unsigned long>(g_filterCommandCount));

  Serial.printf(
      "CAN: running=%s rx=%lu ext=%lu rtr=%lu last_age=%lums\n",
      g_canRunning ? "yes" : "no",
      static_cast<unsigned long>(g_canRxCount),
      static_cast<unsigned long>(g_canExtendedCount),
      static_cast<unsigned long>(g_canRtrCount),
      static_cast<unsigned long>(
          g_lastCanFrameMs == 0 ? 0 : now - g_lastCanFrameMs));
  Serial.printf(
      "CAN recovery: starts=%lu failures=%lu restarts=%lu busoff=%lu faults=%lu\n",
      static_cast<unsigned long>(g_canStartAttempts),
      static_cast<unsigned long>(g_canStartFailures),
      static_cast<unsigned long>(g_canRestartCount),
      static_cast<unsigned long>(g_canBusOffCount),
      static_cast<unsigned long>(g_canFaultCount));
  Serial.printf(
      "CAN loss: invalid_dlc=%lu queue_full=%lu missed=%lu slot_evict=%lu\n",
      static_cast<unsigned long>(g_canInvalidDlcCount),
      static_cast<unsigned long>(g_canRxQueueFullCount),
      static_cast<unsigned long>(g_canRxMissedCount),
      static_cast<unsigned long>(g_canSlotEvictions));
  Serial.printf(
      "TWAI: state=%u TEC=%u REC=%u rx_q=%u tx_q=%u\n",
      static_cast<unsigned>(g_lastTwaiStatus.state),
      static_cast<unsigned>(g_lastTwaiStatus.tx_error_counter),
      static_cast<unsigned>(g_lastTwaiStatus.rx_error_counter),
      static_cast<unsigned>(g_lastTwaiStatus.msgs_to_rx),
      static_cast<unsigned>(g_lastTwaiStatus.msgs_to_tx));

  Serial.printf(
      "GPS: configured=%s fix=%s baud=%lu sentences=%lu parse_fail=%lu age=%lums\n",
      g_gpsConfigured ? "yes" : "no",
      g_gpsValidFix ? "yes" : "no",
      static_cast<unsigned long>(g_gpsCurrentBaud),
      static_cast<unsigned long>(g_gpsSentenceCount),
      static_cast<unsigned long>(g_gpsParseFailureCount),
      static_cast<unsigned long>(
          g_gpsLastSentenceMs == 0 ? 0 : now - g_gpsLastSentenceMs));
  Serial.printf("GPS solution:   sats=%d hdop=%.1f lat=%.7f lon=%.7f\n",
                g_ggaSatellites, g_ggaHdop,
                g_rmcLatitudeDeg, g_rmcLongitudeDeg);
#if GPS_PPS_GPIO >= 0
  Serial.printf("PPS:            count=%lu locked=%s age=%lums\n",
                static_cast<unsigned long>(g_ppsProcessedCount),
                g_ppsLocked ? "yes" : "no",
                static_cast<unsigned long>(
                    g_ppsLastProcessedMs == 0
                        ? 0
                        : now - g_ppsLastProcessedMs));
#else
  Serial.println("PPS:            disabled");
#endif

  Serial.printf("Oil:            %.4f V %.1f psi flags=0x%02X\n",
                g_oilFilteredVolts, g_oilPsi,
                static_cast<unsigned>(g_oilFlags));
  Serial.printf("Heap:           free=%u min=%u bytes\n",
                static_cast<unsigned>(
                    heap_caps_get_free_size(MALLOC_CAP_8BIT)),
                static_cast<unsigned>(
                    heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT)));
  Serial.println("=================");
}

static void showMap() {
  Serial.println("=== Routing ===");
  Serial.printf("Profile mode: %s\n",
                g_profileEnabled ? "ON" : "OFF");
  Serial.printf("RaceChrono filter: active=%s allow_all=%s requested=%u\n",
                g_raceChronoFilterActive ? "yes" : "no",
                g_raceChronoAllowAll ? "yes" : "no",
                static_cast<unsigned>(requestedPidCount()));

  if (g_raceChronoFilterActive && !g_raceChronoAllowAll) {
    size_t printed = 0;
    for (size_t i = 0;
         i < MAX_REQUESTED_PIDS && printed < 64;
         ++i) {
      if (!g_requestedPids[i].used) continue;
      Serial.printf("  RC 0x%03lX @ %u ms\n",
                    static_cast<unsigned long>(
                        g_requestedPids[i].pid),
                    static_cast<unsigned>(
                        g_requestedPids[i].intervalMs));
      ++printed;
    }
  }

  for (uint16_t i = 0; i < g_customDividerCount; ++i) {
    Serial.printf("  CLI 0x%03X div=%u\n",
                  g_customDividers[i].pid,
                  static_cast<unsigned>(
                      g_customDividers[i].divider));
  }

  for (size_t i = 0; i < g_deniedPidCount; ++i) {
    Serial.printf("  DENY 0x%03lX\n",
                  static_cast<unsigned long>(g_deniedPids[i]));
  }
  Serial.println("===============");
}

static bool parsePidAndNumber(const char* input,
                              uint32_t* pid,
                              uint32_t* number) {
  if (input == nullptr || pid == nullptr || number == nullptr) {
    return false;
  }

  char* end = nullptr;
  const unsigned long parsedPid = strtoul(input, &end, 0);
  if (end == input) return false;
  while (*end == ' ' || *end == '\t') ++end;
  if (*end == '\0') return false;

  char* numberEnd = nullptr;
  const unsigned long parsedNumber = strtoul(end, &numberEnd, 0);
  if (numberEnd == end) return false;
  while (*numberEnd == ' ' || *numberEnd == '\t') ++numberEnd;
  if (*numberEnd != '\0') return false;

  *pid = static_cast<uint32_t>(parsedPid);
  *number = static_cast<uint32_t>(parsedNumber);
  return true;
}

static void processCliLine(char* line) {
  if (line == nullptr) return;

  while (*line == ' ' || *line == '\t') ++line;
  size_t length = strlen(line);
  while (length > 0 &&
         (line[length - 1] == ' ' || line[length - 1] == '\t')) {
    line[--length] = '\0';
  }
  if (length == 0) return;

  String command(line);
  command.toUpperCase();

  if (command == "SHOW" || command == "SHOW CFG") {
    showConfig();
    return;
  }
  if (command == "SHOW STATS") {
    showStats();
    return;
  }
  if (command == "SHOW MAP" || command == "SHOW DENY") {
    showMap();
    return;
  }
  if (command == "BLE STATUS") {
    Serial.printf(
        "BLE connected=%s advertising=%s CAN_sub=%s GPS_sub=%s TIME_sub=%s\n",
        isBleConnected() ? "yes" : "no",
        (g_bleAdvertising != nullptr &&
         g_bleAdvertising->isAdvertising())
            ? "yes"
            : "no",
        g_canSubscribed ? "yes" : "no",
        g_gpsSubscribed ? "yes" : "no",
        g_gpsTimeSubscribed ? "yes" : "no");
    return;
  }
  if (command == "CAN RESTART") {
    scheduleCanRestart(millis(), "operator command");
    g_canNextStartMs = millis() + 50u;
    return;
  }
  if (command == "PROFILE ON") {
    g_profileEnabled = true;
    Serial.println("Profile=GR86 allow-list (not saved)");
    return;
  }
  if (command == "PROFILE OFF") {
    g_profileEnabled = false;
    Serial.println("Profile=sniff-all (not saved)");
    return;
  }
  if (command == "CLEAR FILTERS") {
    clearRaceChronoFilter();
    clearDeniedPids();
    Serial.println("Runtime RaceChrono/deny filters cleared");
    return;
  }

  if (command.startsWith("RATE ")) {
    const uint32_t rate = static_cast<uint32_t>(
        strtoul(line + 5, nullptr, 0));
    if (rate < 10u || rate > 2000u) {
      Serial.println("RATE range is 10..2000 ms");
    } else {
      g_oilPublishPeriodMs = static_cast<uint16_t>(rate);
      Serial.printf("Oil rate=%u ms (not saved)\n",
                    static_cast<unsigned>(g_oilPublishPeriodMs));
    }
    return;
  }

  if (command.startsWith("ALLOW ")) {
    uint32_t pid = 0;
    uint32_t divider = 0;
    if (!parsePidAndNumber(line + 6, &pid, &divider) ||
        pid > 0x7FFu || divider < 1u || divider > 255u) {
      Serial.println("Usage: ALLOW <0x000..0x7FF> <1..255>");
      return;
    }

    undenyPid(pid);
    if (!setCustomDivider(pid, static_cast<uint8_t>(divider))) {
      Serial.println("ALLOW failed: custom divider table full");
    } else {
      Serial.printf("ALLOW 0x%03lX div=%lu (not saved)\n",
                    static_cast<unsigned long>(pid),
                    static_cast<unsigned long>(divider));
    }
    return;
  }

  if (command.startsWith("DENY ")) {
    char* end = nullptr;
    const uint32_t pid =
        static_cast<uint32_t>(strtoul(line + 5, &end, 0));
    while (end != nullptr && (*end == ' ' || *end == '\t')) ++end;
    if (end == line + 5 || (end != nullptr && *end != '\0') ||
        pid > 0x1FFFFFFFu) {
      Serial.println("Usage: DENY <pid>");
      return;
    }

    denyPid(pid);
    Serial.printf("DENY 0x%03lX (runtime only)\n",
                  static_cast<unsigned long>(pid));
    return;
  }

  if (command == "CAL SHOW") {
    OilCalibrationRaw raw = {};
    if (!oil_calibration_read_raw(&raw) || !raw.present) {
      Serial.printf("Oil calibration: defaults %.4f / %.4f V\n",
                    g_oilV0Adc, g_oilV1Adc);
    } else {
      Serial.printf(
          "Oil calibration: version=%lu V0=%.4f V1=%.4f valid=%s "
          "CRC=%08lX/%08lX\n",
          static_cast<unsigned long>(raw.version),
          raw.v0_adc, raw.v1_adc,
          raw.valid ? "yes" : "no",
          static_cast<unsigned long>(raw.stored_crc32),
          static_cast<unsigned long>(raw.computed_crc32));
    }
    return;
  }

  if (command == "CAL 0") {
    const float sample = readOilFilteredVolts();
    if (!isfinite(sample) || sample >= g_oilV1Adc) {
      Serial.println("CAL 0 refused: invalid/inverted endpoint");
      return;
    }

    g_oilV0Adc = sample;
    const bool saved =
        oil_calibration_save(g_oilV0Adc, g_oilV1Adc);
    Serial.printf("Oil V0=%.4f V (%s)\n",
                  g_oilV0Adc, saved ? "saved" : "save failed");
    return;
  }

  if (command == "CAL 1") {
    const float sample = readOilFilteredVolts();
    if (!isfinite(sample) || sample <= g_oilV0Adc) {
      Serial.println("CAL 1 refused: invalid/inverted endpoint");
      return;
    }

    g_oilV1Adc = sample;
    const bool saved =
        oil_calibration_save(g_oilV0Adc, g_oilV1Adc);
    Serial.printf("Oil V1=%.4f V (%s)\n",
                  g_oilV1Adc, saved ? "saved" : "save failed");
    return;
  }

  if (command == "SAVE") {
    Serial.println(saveRuntimeConfig()
                       ? "Saved profile/rate/dividers."
                       : "SAVE failed.");
    showConfig();
    return;
  }

  if (command == "LOAD") {
    loadRuntimeConfig();
    loadOilCalibration();
    Serial.println("Reloaded persistent configuration.");
    showConfig();
    return;
  }

  if (command == "RESETCFG") {
    if (g_prefs.begin(CFG_NAMESPACE, false)) {
      ScopedNvsWrite writeGuard;
      g_prefs.clear();
      g_prefs.end();
    }

    g_profileEnabled = true;
    g_oilPublishPeriodMs = 40;
    clearCustomDividers();
    clearDeniedPids();
    clearRaceChronoFilter();
    g_oilV0Adc = DEFAULT_OIL_V0_ADC;
    g_oilV1Adc = DEFAULT_OIL_V1_ADC;
    oil_calibration_save(g_oilV0Adc, g_oilV1Adc);
    saveRuntimeConfig();
    Serial.println("Configuration reset to stability defaults.");
    showConfig();
    return;
  }

  Serial.println(
      "Commands: SHOW [CFG|STATS|MAP] | BLE STATUS | CAN RESTART | "
      "PROFILE ON|OFF | CLEAR FILTERS | RATE <ms> | "
      "ALLOW <pid> <div> | DENY <pid> | "
      "CAL 0|1|SHOW | SAVE | LOAD | RESETCFG");
}

static void serviceSerialCli() {
  static char buffer[192] = {};
  static size_t length = 0;
  static bool overflow = false;

  while (Serial.available()) {
    const int raw = Serial.read();
    if (raw < 0) break;

    if (raw == '\r' || raw == '\n') {
      if (overflow) {
        Serial.println("CLI line too long; ignored.");
      } else if (length > 0) {
        buffer[length] = '\0';
        processCliLine(buffer);
      }
      length = 0;
      overflow = false;
      continue;
    }

    if (length < sizeof(buffer) - 1) {
      buffer[length++] = static_cast<char>(raw);
    } else {
      overflow = true;
    }
  }
}

// -----------------------------------------------------------------------------
// Arduino entry points
// -----------------------------------------------------------------------------

static void setupImpl() {
  Serial.begin(115200);
  const uint32_t serialStart = millis();
  while (!Serial && millis() - serialStart < 1000u) {
    delay(10);
  }

  g_bootResetReason = esp_reset_reason();

  Serial.println();
  Serial.println("==============================================");
  Serial.println("GR86 CCA telemetry stability firmware");
  Serial.printf("Build: %s\n", BUILD_ID);
  Serial.printf("Boot reason: %s (%d)\n",
                resetReasonName(g_bootResetReason),
                static_cast<int>(g_bootResetReason));
  Serial.println("==============================================");

  initWatchdog();

  led_init();
  led_set_power(LedPattern::Solid);
  led_set_ble(LedPattern::BlinkFast);
  led_set_can(LedPattern::BlinkSlow);
  led_set_gps(LedPattern::BlinkSlow);
  led_set_sys(LedPattern::Off);
  led_set_oil(LedPattern::Off);
  led_service(millis());

  analogReadResolution(12);
  analogSetPinAttenuation(OIL_ADC_PIN, ADC_11db);
  pinMode(OIL_ADC_PIN, INPUT);

  loadRuntimeConfig();
  loadOilCalibration();

#if GPS_PPS_GPIO >= 0
  pinMode(GPS_PPS_GPIO, INPUT_PULLDOWN);
  attachInterrupt(GPS_PPS_GPIO, onGpsPps, RISING);
  Serial.printf("GPS: PPS on GPIO %d\n", GPS_PPS_GPIO);
#endif

  initBle();

  startGpsProbe(0, millis());

  g_canNextStartMs = 0;
  serviceCanStart(millis());

  showConfig();
}

static void loopImpl() {
  esp_task_wdt_reset();

  const uint32_t now = millis();

  // BLE service first: connection maintenance never waits on CAN/GPS.
  startAdvertisingIfNeeded(now);

  serviceCanStart(now);
  serviceCanHealth(now);
  serviceCanReceive(now);

  serviceOil(now);
  publishDiagnostics(now);

  // GPS gets priority within the shared BLE budget; coalesced CAN uses the
  // remainder. This prevents a busy CAN bus from starving lap-position data.
  serviceGps(now);
  serviceCanForwarding(now);

  serviceStatusLeds(now);
  serviceSerialCli();

  // Yield to NimBLE/Arduino tasks without introducing a blocking recovery loop.
  delay(1);
}

}  // namespace cca

void setup() {
  cca::setupImpl();
}

void loop() {
  cca::loopImpl();
}
