#pragma once
/** Borosil RMP DWIN T5L DGUS II driver; active contract: DGUS Assets v3. */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
namespace rmp {
constexpr uint16_t DWIN_PANEL_WIDTH=320, DWIN_PANEL_HEIGHT=480;
constexpr uint8_t DWIN_PANEL_ROTATION=0;
constexpr uint8_t DWIN_PAGE_BOOT=0, DWIN_PAGE_IDLE=1, DWIN_PAGE_ASSIGNMENT=2,
                  DWIN_PAGE_WIFI_SETUP=3, DWIN_PAGE_UNBOUND=4,
                  DWIN_PAGE_PRESTART=5, DWIN_PAGE_RUNNING=6,
                  DWIN_PAGE_ALARM=7, DWIN_PAGE_COMPLETED=8,
                  DWIN_PAGE_DIAGNOSTICS=9;
constexpr uint16_t VP_FW_VERSION=0x1060, VP_TEMP_VALUE=0x1100,
  VP_RPM_VALUE=0x1130, VP_TORQUE_VALUE=0x1140, VP_ALARM_RATE=0x1170,
  VP_ALARM_PARAM=0x1180, VP_ALARM_TEMP=0x1190, VP_ALARM_LIMIT=0x11A0,
  VP_DURATION=0x11C0, VP_REACTOR_TITLE=0x2000, VP_LAB_NAME=0x2020,
  VP_CLOCK=0x2040, VP_DEVICE_UUID=0x2050, VP_ANALYST_NAME=0x3000,
  VP_PROCESS_NAME=0x3020, VP_MAX_TEMP=0x3080, VP_MAX_SPEED=0x3090,
  VP_MAX_ROC=0x30A0, VP_TOTAL_DURATION=0x3100, VP_FINAL_TEMP=0x3110,
  VP_SAMPLES_LOGGED=0x3120, VP_IP_ADDRESS=0x3210, VP_MQTT_BROKER=0x3220,
  VP_MAC_ADDRESS=0x3280, VP_DIAG_VALUE_BASE=0x3290,
  VP_DIAG_CAPTION_BASE=0x3300;
constexpr uint16_t VP_TEMP_QUAL_PILL=0x1301, VP_BOOT_PROGRESS=0x1306,
  VP_RUN_FOOTER=0x1307, VP_ALARM_FLASH=0x1308, VP_MUTE_BUTTON=0x1309,
  VP_AUDIT_STATE=0x130A, VP_DIAG_DOT_BASE=0x1310,
  VP_DIAG_ROW_BASE=0x1320, VP_DIAG_SCROLL=0x1325,
  VP_BTN_ACCEPT=0x1330, VP_BTN_REJECT=0x1331, VP_BTN_START=0x1332,
  VP_BTN_CANCEL=0x1333, VP_BTN_RETURN=0x1334;
// Retired by v3 and intentionally absent: 0x1110,0x1120,0x1150,0x1160,
// 0x11B0,0x11D0,0x1300,0x1305,0x1315-0x1318,0x2010,0x2018,
// 0x3010-0x3070,0x3200,0x3230-0x3270.
enum DotStatus:uint16_t { DOT_GOOD=0, DOT_SUSPECT=1, DOT_BAD=2, DOT_OFF=3 };
class Dwin {
 public:
  void begin(); void setPage(uint8_t page); uint8_t currentPage() const{return current_page_;}
  void readPageRequest(); void pollRx(); void writeText(uint16_t,const char*,size_t=32);
  void writeValue(uint16_t,uint16_t); void writeNavigationState(uint16_t,uint16_t,uint16_t,uint16_t);
  void writePowerUpDefaults(); void sendRaw(const uint8_t*,size_t);
  void showBootPage(uint8_t,const char*);
  void showIdlePage(const char*,const char*,const char*,bool,uint16_t,float,float,bool,float,float,bool,const char* = nullptr);
  void showUnboundPage(const char*,const char*,const char*,const char*);
  void showAssignmentPage(const char*,const char*,const char*,const char*);
  void showPreStartPage(const char*,const char*,const char*,const char*,float,float,float);
  void showRunningPage(const char*,const char*,const char*,const char*,const char*,bool,uint16_t,float,float,bool,float,float,float,uint8_t,bool,float,const char*,const char*,uint8_t,bool,const char* = nullptr);
  void showAlarmPage(const char*,float,float,float,bool,bool);
  void showBatchCompletedPage(const char*,const char*,const char*,const char*,const char*,float,uint32_t,bool);
  void showDiagnosticsPage(const char*,DotStatus,const char*,DotStatus,const char*,DotStatus,const char*,DotStatus,const char*,DotStatus,const char*,DotStatus,const char*,DotStatus,const char*,DotStatus,const char*,DotStatus);
 private:
  uint8_t current_page_=DWIN_PAGE_BOOT, diagnostics_window_top_=0; void* mutex_=nullptr;
  void lock(); void unlock();
};
}
