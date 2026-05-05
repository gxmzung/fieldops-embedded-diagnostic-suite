#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

typedef void (*task_fn)(uint32_t now_ms);

typedef struct {
    const char* name;
    uint32_t period_ms;
    uint32_t last_run_ms;
    task_fn run;
} task_t;

static void sensor_read(uint32_t now_ms) {
    printf("[%06u ms] sensor_read: temperature/voltage sampled\n", now_ms);
}

static void telemetry_send(uint32_t now_ms) {
    printf("[%06u ms] telemetry_send: packet queued\n", now_ms);
}

static void health_check(uint32_t now_ms) {
    printf("[%06u ms] health_check: state=NORMAL\n", now_ms);
}

static void log_flush(uint32_t now_ms) {
    printf("[%06u ms] log_flush: buffered logs persisted\n", now_ms);
}

static void watchdog_check(uint32_t now_ms) {
    printf("[%06u ms] watchdog_check: tasks alive\n", now_ms);
}

static task_t tasks[] = {
    {"Sensor Read",    100, 0, sensor_read},
    {"Telemetry Send", 500, 0, telemetry_send},
    {"Health Check", 1000, 0, health_check},
    {"Log Flush",    2000, 0, log_flush},
    {"Watchdog",     1000, 0, watchdog_check},
};

int main(void) {
    const uint32_t tick_ms = 100;
    const uint32_t end_ms = 5000;
    const size_t task_count = sizeof(tasks) / sizeof(tasks[0]);

    printf("FDU-01 embedded task scheduler demo started\n");

    for (uint32_t now = 0; now <= end_ms; now += tick_ms) {
        for (size_t i = 0; i < task_count; i++) {
            if (now == 0 || now - tasks[i].last_run_ms >= tasks[i].period_ms) {
                tasks[i].run(now);
                tasks[i].last_run_ms = now;
            }
        }
    }

    printf("scheduler demo completed\n");
    return 0;
}
