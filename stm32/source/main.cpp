/* mbed Microcontroller Library
 * Copyright (c) 2006-2015 ARM Limited
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


#include <events/mbed_events.h>
#include "ble/BLE.h"
#include "ble/gap/Gap.h"
#include "ble/services/HeartRateService.h"
#include "ble/services/MagnetometerService.h"
#include "ble/services/ToFService.h"
#include "pretty_printer.h"
#include "mbed-trace/mbed_trace.h"
#include "stm32l475e_iot01_magneto.h"

using namespace std::literals::chrono_literals;

const static char DEVICE_NAME[] = "Heartrate_team5";

static events::EventQueue event_queue(/* event count */ 16 * EVENTS_EVENT_SIZE);

//###############################################################
static DevI2C devI2c(PB_11,PB_10);
// static DevI2C devI2c_2(D14,D15);

/* Range sensor - B-L475E-IOT01A2 only */
static DigitalOut shutdown_pin(PC_6);
static class VL53L0X VL53L0X_1(&devI2c, &shutdown_pin, PC_7);
//###############################################################


class HeartrateDemo : ble::Gap::EventHandler {
public:
    HeartrateDemo(BLE &ble, events::EventQueue &event_queue) :
        _ble(ble),
        _event_queue(event_queue),
        _heartrate_uuid(GattService::UUID_HEART_RATE_SERVICE),
        _magnetometer_uuid(GattService::UUID_MAGNETO_SERVICE),
        _tof_uuid(GattService::UUID_DISTANCE_SERVICE),
        _heartrate_value(100),
        _heartrate_service(ble, _heartrate_value, HeartRateService::LOCATION_FINGER),
        _magneto_service(_ble, -1, -1, -1),
        _tof_service(_ble, 0),
        _adv_data_builder(_adv_buffer),
        _pDataXYZ{0}    
    {
    }
    
    //void printHeartRateValue() {
    //    uint16_t heartRate = _heartrate_service.getHeartRateValue();
    //    printf("Heart Rate: %d BPM\n", heartRate);
    //}
    void start()
    {
        _ble.init(this, &HeartrateDemo::on_init_complete);
        VL53L0X_1.init_sensor(VL53L0X_DEFAULT_ADDRESS);
        VL53L0X_1.range_start_continuous_mode(); 
        _event_queue.dispatch_forever();
        
    }

private:
    /** Callback triggered when the ble initialization process has finished */
    void on_init_complete(BLE::InitializationCompleteCallbackContext *params)
    {
        if (params->error != BLE_ERROR_NONE) {
            printf("Ble initialization failed.");
            return;
        }

        print_mac_address();

        /* this allows us to receive events like onConnectionComplete() */
        _ble.gap().setEventHandler(this);

        /* heart rate value updated every second */
        _event_queue.call_every(
            300ms,
            [this] {
                update_sensor_value();
            }
        );

        start_advertising();
    }

    void start_advertising()
    {
        /* Create advertising parameters and payload */

        ble::AdvertisingParameters adv_parameters(
            ble::advertising_type_t::CONNECTABLE_UNDIRECTED,
            ble::adv_interval_t(ble::millisecond_t(100))
        );

        _adv_data_builder.setFlags();
        _adv_data_builder.setAppearance(ble::adv_data_appearance_t::GENERIC_HEART_RATE_SENSOR);
        _adv_data_builder.setLocalServiceList({&_heartrate_uuid, 1});
        _adv_data_builder.setLocalServiceList({&_magnetometer_uuid, 1});
        _adv_data_builder.setName(DEVICE_NAME);

        /* Setup advertising */

        ble_error_t error = _ble.gap().setAdvertisingParameters(
            ble::LEGACY_ADVERTISING_HANDLE,
            adv_parameters
        );

        if (error) {
            printf("_ble.gap().setAdvertisingParameters() failed\r\n");
            return;
        }

        error = _ble.gap().setAdvertisingPayload(
            ble::LEGACY_ADVERTISING_HANDLE,
            _adv_data_builder.getAdvertisingData()
        );

        if (error) {
            printf("_ble.gap().setAdvertisingPayload() failed\r\n");
            return;
        }

        /* Start advertising */

        error = _ble.gap().startAdvertising(ble::LEGACY_ADVERTISING_HANDLE);

        if (error) {
            printf("_ble.gap().startAdvertising() failed\r\n");
            return;
        }

        printf("Heart rate sensor advertising, please connect\r\n");
    }

    void update_sensor_value()
    {
        /* you can read in the real value but here we just simulate a value */
        _heartrate_value++;
        BSP_MAGNETO_GetXYZ(_pDataXYZ);

        status = VL53L0X_1.get_measurement(range_continuous_polling, &measurement_data_1);
        _distance = measurement_data_1.RangeMilliMeter;
        // printf("distance = %d [mm]", _distance);
   

        // printf("\nMAGNETO_X = %d\n", _pDataXYZ[0]);
        // printf("MAGNETO_Y = %d\n", _pDataXYZ[1]);
        // printf("MAGNETO_Z = %d\n", _pDataXYZ[2]);

        /*  60 <= bpm value < 110 */
        if (_heartrate_value == 110) {
            _heartrate_value = 60;
        }
        
        // _heartrate_service.updateHeartRate(_heartrate_value);
        // _magneto_service.updateMagnometerRate(_pDataXYZ[0], _pDataXYZ[1], _pDataXYZ[2]);
        _tof_service.updateDistance(_distance);
    }


    /* these implement ble::Gap::EventHandler */
private:
    /* when we connect we stop advertising, restart advertising so others can connect */
    virtual void onConnectionComplete(const ble::ConnectionCompleteEvent &event)
    {
        if (event.getStatus() == ble_error_t::BLE_ERROR_NONE) {
            printf("Client connected, you may now subscribe to updates\r\n");
        }
    }

    /* when we connect we stop advertising, restart advertising so others can connect */
    virtual void onDisconnectionComplete(const ble::DisconnectionCompleteEvent &event)
    {
        printf("Client disconnected, restarting advertising\r\n");

        ble_error_t error = _ble.gap().startAdvertising(ble::LEGACY_ADVERTISING_HANDLE);

        if (error) {
            printf("_ble.gap().startAdvertising() failed\r\n");
            return;
        }
    }

private:
    BLE &_ble;
    events::EventQueue &_event_queue;

    UUID _heartrate_uuid;
    UUID _magnetometer_uuid;
    UUID _tof_uuid;

    uint16_t _heartrate_value;
    HeartRateService _heartrate_service;
    MagnetometerService _magneto_service;
    ToFService _tof_service;

    uint8_t _adv_buffer[ble::LEGACY_ADVERTISING_MAX_SIZE];
    ble::AdvertisingDataBuilder _adv_data_builder;

    int16_t _pDataXYZ[3];

    uint16_t _distance;
    VL53L0X_RangingMeasurementData_t measurement_data_1;
    int status;
};

/* Schedule processing of events from the BLE middleware in the event queue. */
void schedule_ble_events(BLE::OnEventsToProcessCallbackContext *context)
{
    event_queue.call(Callback<void()>(&context->ble, &BLE::processEvents));
}

int main()
{
    mbed_trace_init();
    BSP_MAGNETO_Init();
    BLE &ble = BLE::Instance();
    
    ble.onEventsToProcess(schedule_ble_events);

    HeartrateDemo demo(ble, event_queue);
    demo.start();

    return 0;
}
