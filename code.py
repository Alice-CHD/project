class HighwayOperationScenarios:
    """高速公路运营情景分类"""

    def __init__(self):
        self.scenarios = {
            'manual_driving': {'levels': ['L0', 'L1'], 'vehicle_types': ['fuel', 'electric']},
            'smart_vehicle_mixing': {'levels': ['L2', 'L3'], 'vehicle_types': ['smart_fuel', 'smart_electric']},
            'vehicle_platooning': {'levels': ['L4', 'L5'], 'vehicle_types': ['platoon_fuel', 'platoon_electric']}
        }

    def get_scenario_parameters(self, scenario_name):
        """获取特定情景的参数"""
        return self.scenarios.get(scenario_name, {})


"__________________________________________________________________________"



import numpy as np

class FuelVehicleEmissionModel:
    """燃油车碳排放测算模型"""

    def __init__(self):
        # 模型参数
        self.mass_factor = 1.1  # 质量因子ε
        self.gravity = 9.81  # 重力加速度
        self.rolling_resistance = 0.015  # 滚动阻力系数Cw
        self.air_density = 1.2  # 空气密度
        self.drag_coefficient = 0.3  # 风的阻力系数Cr
        self.frontal_area = 2.0  # 挡风玻璃面积
        self.friction_coefficient = 0.01  # 内部摩擦系数Ci

    def calculate_vsp(self, velocity, acceleration, road_angle=0, wind_speed=0):
        """
        计算机动车比功率(VSP)
        公式3.1和3.2
        """
        # 动能变化项
        kinetic_term = velocity * acceleration

        # 势能变化项
        potential_term = velocity * self.gravity * np.sin(road_angle)

        # 滚动阻力项
        rolling_term = velocity * self.rolling_resistance * self.gravity * np.cos(road_angle)

        # 空气阻力项
        air_resistance = 0.5 * self.air_density * self.drag_coefficient * self.frontal_area * (
                    velocity + wind_speed) ** 2
        air_term = velocity * air_resistance / (self.mass_factor * 1000)  # 转换为kW/t

        vsp = kinetic_term + potential_term + rolling_term + air_term
        return vsp

    def vsp_bin_classification(self, vsp_value):
        """VSP区间分类"""
        bins = [
            (-np.inf, -2), (-2, 0), (0, 1), (1, 4), (4, 7), (7, 10),
            (10, 13), (13, 16), (16, 19), (19, 23), (23, 28), (28, 33), (33, np.inf)
        ]

        for i, (low, high) in enumerate(bins):
            if low <= vsp_value < high:
                return i
        return len(bins) - 1

    def calculate_co2_emission(self, velocity_profile, acceleration_profile, duration):
        """
        计算CO2排放总量
        公式3.3
        """
        total_emission = 0
        emission_rates = self._get_emission_rate_table()

        for t in range(len(velocity_profile)):
            v = velocity_profile[t]
            a = acceleration_profile[t]

            vsp = self.calculate_vsp(v, a)
            bin_index = self.vsp_bin_classification(vsp)

            # 获取该VSP区间的排放速率
            emission_rate = emission_rates[bin_index]
            total_emission += emission_rate * duration[t]

        return total_emission

    def _get_emission_rate_table(self):
        """获取VSP区间对应的排放速率表"""
        # 这里应该根据实际标定数据填充
        return [0.1, 0.2, 0.3, 0.5, 0.8, 1.2, 1.8, 2.5, 3.2, 4.0, 5.0, 6.0, 7.0]



"__________________________________________________________________________"


class ElectricVehicleEmissionModel:
    """电动车碳排放测算模型"""

    def __init__(self):
        self.transmission_efficiency = 0.9  # 传动系统效率η
        self.rolling_resistance_coef = 0.015  # 滚动阻力系数μ
        self.drag_coefficient = 0.3  # 空气阻力系数Cd
        self.frontal_area = 2.0  # 迎风面积A
        self.rotational_mass_factor = 1.05  # 旋转质量换算系数δ
        self.power_plant_emission = 293.4  # 电厂每度电碳排放(克/千瓦时)
        self.grid_loss_rate = 0.07  # 电网传输损耗率

    def calculate_instant_power_consumption(self, velocity, acceleration):
        """
        计算电动车瞬时电耗
        公式3.4
        """
        # 滚动阻力功率
        rolling_power = self.rolling_resistance_coef * velocity

        # 空气阻力功率
        air_power = 0.5 * self.drag_coefficient * self.frontal_area * velocity ** 3

        # 加速功率
        acceleration_power = self.rotational_mass_factor * velocity * acceleration

        total_power = (rolling_power + air_power + acceleration_power) / self.transmission_efficiency
        return max(total_power, 0)  # 功率不能为负

    def calculate_co2_equivalent(self, power_consumption_kwh, time_hours):
        """
        计算CO2当量排放
        公式3.5-3.7
        """
        # 考虑电网传输损耗
        actual_consumption = power_consumption_kwh / (1 - self.grid_loss_rate)

        # 考虑火电比例(70%)
        thermal_power_ratio = 0.7
        thermal_consumption = actual_consumption * thermal_power_ratio

        # 计算CO2排放
        co2_emission = thermal_consumption * self.power_plant_emission

        return co2_emission

    def calculate_total_emission(self, velocity_profile, acceleration_profile, time_intervals):
        """
        计算总碳排放量
        """
        total_power = 0

        for i in range(len(velocity_profile)):
            instant_power = self.calculate_instant_power_consumption(
                velocity_profile[i], acceleration_profile[i]
            )
            # 转换为千瓦时
            power_kwh = instant_power * time_intervals[i] / 3600 / 1000
            total_power += power_kwh

        total_emission = self.calculate_co2_equivalent(total_power,
                                                       sum(time_intervals) / 3600)
        return total_emission



"__________________________________________________________________________"


class SmartVehicleMixingModel:
    """智能车混入情景碳排放模型"""

    def __init__(self):
        self.air_resistance_correction = AirResistanceCorrection()

    def calculate_mixed_traffic_emission(self, scenario_params, traffic_data):
        """
        计算智能车混入后的交通流总碳排放
        公式3.8
        """
        total_emission = 0

        # 人工驾驶燃油车排放
        for fuel_vehicle in traffic_data['fuel_vehicles']:
            emission = self._calculate_fuel_vehicle_emission(fuel_vehicle)
            total_emission += emission

        # 智能电动车排放
        for smart_electric in traffic_data['smart_electric_vehicles']:
            emission = self._calculate_smart_electric_emission(smart_electric)
            total_emission += emission

        # 智能燃油车排放
        for smart_fuel in traffic_data['smart_fuel_vehicles']:
            emission = self._calculate_smart_fuel_emission(smart_fuel)
            total_emission += emission

        return total_emission

    def calculate_lane_specific_emission(self, lane_type, mixing_ratio, traffic_flow):
        """
        分车道碳排放测算
        公式3.9
        """
        lane_emissions = {}

        lanes = ['L1', 'L2', 'L3']  # 外侧、中间、内侧车道

        for lane in lanes:
            lane_data = traffic_flow.get_lane_data(lane)
            emission = self._calculate_lane_emission(lane_data, mixing_ratio)
            lane_emissions[lane] = emission

        return lane_emissions

    def calculate_smart_lane_emission(self, platoon_data, dedicated_lane=True):
        """
        基于智能车专用道的碳排放测算
        公式3.14-3.15
        """
        if dedicated_lane:
            # 应用空气阻力修正
            corrected_data = self.air_resistance_correction.apply_platoon_correction(platoon_data)
        else:
            corrected_data = platoon_data

        total_emission = 0
        for vehicle in corrected_data['vehicles']:
            if vehicle['type'] == 'smart_electric':
                emission = self._calculate_corrected_electric_emission(vehicle)
            elif vehicle['type'] == 'smart_fuel':
                emission = self._calculate_corrected_fuel_emission(vehicle)
            else:
                emission = self._calculate_fuel_vehicle_emission(vehicle)

            total_emission += emission

        return total_emission


class AirResistanceCorrection:
    """空气阻力修正系数计算"""

    def calculate_head_vehicle_correction(self, vehicle_spacing):
        """
        头车空气阻力修正系数
        公式3.10
        """
        μ = 0.8 * np.exp(-0.02 * vehicle_spacing) + 0.2
        return μ

    def calculate_following_vehicle_correction(self, vehicle_spacing):
        """
        跟随车空气阻力修正系数
        公式3.11
        """
        β = 0.6 * np.exp(-0.03 * vehicle_spacing) + 0.4
        return β

    def apply_platoon_correction(self, platoon_data):
        """应用队列空气阻力修正"""
        corrected_data = platoon_data.copy()

        for i, vehicle in enumerate(corrected_data['vehicles']):
            if i == 0:  # 头车
                spacing = vehicle['spacing_to_follower']
                correction_factor = self.calculate_head_vehicle_correction(spacing)
            else:  # 跟随车
                spacing = vehicle['spacing_to_leader']
                correction_factor = self.calculate_following_vehicle_correction(spacing)

            vehicle['air_resistance_correction'] = correction_factor
            vehicle['corrected_drag_coefficient'] = (vehicle.get('original_drag_coefficient', 0.3)
                                                     * correction_factor)

        return corrected_data





"__________________________________________________________________________"





class VehiclePlatooningModel:
    """车辆队列行驶碳排放模型"""

    def __init__(self):
        self.acc_model = ACCModel()
        self.cacc_model = CACCModel()

    def calculate_electric_platoon_emission(self, platoon_config, traffic_conditions):
        """
        电动车队列碳排放测算
        公式3.21-3.22
        """
        if platoon_config['platoon_size'] < 2:
            # 无法形成队列的情况
            return self._calculate_non_platoon_emission(platoon_config)
        else:
            # 形成队列的情况
            return self._calculate_platoon_emission(platoon_config, traffic_conditions)

    def calculate_mixed_fuel_ratio_emission(self, platoon_data, fuel_ratio):
        """
        基于车队内燃油车辆占比的碳排放测算
        公式3.27-3.28
        """
        total_emission = 0
        platoon_count = platoon_data['platoon_count']

        for i in range(platoon_count):
            platoon = platoon_data['platoons'][i]
            platoon_emission = self._calculate_single_platoon_emission(platoon, fuel_ratio)
            total_emission += platoon_emission

        return total_emission

    def calculate_desired_headway_emission(self, headway_type, degradation_scenario):
        """
        基于智能车辆期望车头时距的碳排放测算
        公式3.23-3.26
        """
        if degradation_scenario == 'human_vehicle_ahead':
            return self._calculate_human_vehicle_ahead_emission(headway_type)
        elif degradation_scenario == 'max_platoon_ahead':
            return self._calculate_max_platoon_ahead_emission(headway_type)
        else:
            return self._calculate_normal_platoon_emission(headway_type)

    def _calculate_non_platoon_emission(self, config):
        """无法形成队列时的排放计算"""
        emission = 0
        for vehicle in config['vehicles']:
            if vehicle['type'] == 'electric':
                emission += self._calculate_electric_vehicle_emission(vehicle)
            else:
                emission += self._calculate_fuel_vehicle_emission(vehicle)
        return emission


class ACCModel:
    """ACC跟驰模型"""

    def __init__(self):
        self.k1 = 0.23  # 调节系数k1
        self.k2 = 0.07  # 调节系数k2

    def calculate_acceleration(self, spacing, speed_difference, desired_time_headway):
        """
        ACC模型加速度计算
        公式参考第四章
        """
        spacing_error = spacing - (desired_time_headway * self.speed + 1 + 5)  # 1为车长，5为拥堵间距
        acceleration = self.k1 * spacing_error + self.k2 * speed_difference
        return acceleration


class CACCModel:
    """CACC跟驰模型"""

    def __init__(self):
        self.kp = 0.45  # 比例系数
        self.kd = 0.25  # 微分系数

    def calculate_speed(self, current_speed, spacing_error, spacing_error_derivative,
                        desired_time_headway):
        """
        CACC模型速度计算
        公式参考第四章
        """
        speed_adjustment = (self.kp * spacing_error +
                            self.kd * spacing_error_derivative)
        new_speed = current_speed + speed_adjustment
        return max(new_speed, 0)


class SmartVehicleLaneChangeModel:
    """智能车换道决策模型"""

    def __init__(self):
        self.lane_utility = LaneUtilityModel()

    def single_vehicle_dynamic_decision(self, vehicle_state, surrounding_vehicles):
        """
        单车动态换道决策
        基于图4-2流程图
        """
        # 换道动机判断
        motivation = self._assess_lane_change_motivation(vehicle_state, surrounding_vehicles)

        if motivation > 0.7:  # 高换道动机
            # 目标间隙接受判断
            gap_acceptance = self._assess_gap_acceptance(vehicle_state, surrounding_vehicles)

            if gap_acceptance:
                return self._execute_lane_change(vehicle_state, surrounding_vehicles)

        return False

    def multi_vehicle_cooperative_decision(self, vehicle_group, communication_data):
        """
        多车协同换道决策
        基于图4-4流程图
        """
        # 车辆状态同步
        synchronized_states = self._synchronize_vehicle_states(vehicle_group, communication_data)

        # 联合轨迹规划
        joint_trajectory = self._plan_joint_trajectory(synchronized_states)

        # 安全性验证
        if self._validate_safety(joint_trajectory):
            return self._execute_cooperative_lane_change(joint_trajectory)

        return False

    def _assess_lane_change_motivation(self, vehicle, surroundings):
        """评估换道动机"""
        current_lane_utility = self.lane_utility.calculate_lane_utility(
            vehicle['current_lane'], vehicle, surroundings)

        target_lane_utility = self.lane_utility.calculate_lane_utility(
            vehicle['target_lane'], vehicle, surroundings)

        motivation = max(0, target_lane_utility - current_lane_utility)
        return motivation

    def _assess_gap_acceptance(self, vehicle, surroundings):
        """评估间隙接受概率"""
        front_gap = surroundings['target_front_gap']
        rear_gap = surroundings['target_rear_gap']

        desired_front_gap = self._calculate_desired_front_gap(vehicle)
        desired_rear_gap = self._calculate_desired_rear_gap(vehicle)

        front_acceptance = front_gap >= desired_front_gap
        rear_acceptance = rear_gap >= desired_rear_gap

        return front_acceptance and rear_acceptance


class LaneUtilityModel:
    """车道效用计算模型"""

    def calculate_lane_utility(self, lane_type, vehicle, surroundings):
        """
        计算车道效用值
        公式参考第四章
        """
        speed_utility = self._calculate_speed_utility(lane_type, vehicle)
        freedom_utility = self._calculate_freedom_utility(lane_type, surroundings)
        safety_utility = self._calculate_safety_utility(lane_type, surroundings)

        total_utility = (0.5 * speed_utility +
                         0.3 * freedom_utility +
                         0.2 * safety_utility)

        return total_utility

    def _calculate_speed_utility(self, lane_type, vehicle):
        """速度效用计算"""
        if lane_type == 'inner':
            return vehicle['desired_speed'] / 120  # 内侧车道速度效用高
        elif lane_type == 'middle':
            return vehicle['desired_speed'] / 100
        else:  # outer
            return vehicle['desired_speed'] / 80




"__________________________________________________________________________"




class HeterogeneousTrafficFlowModel:
    """异质交通流基本图模型"""

    def __init__(self):
        self.parameters = {
            'human_driver_headway': 2.0,  # 人工驾驶车头时距
            'acc_headway': 1.5,  # ACC车头时距
            'cacc_headway': 1.0,  # CACC车头时距
            'vehicle_length': 5.0,  # 车辆长度
            'min_spacing': 2.0  # 最小间距
        }

    def calculate_fundamental_diagram(self, smart_vehicle_ratio, max_platoon_size=3):
        """
        计算异质交通流基本图
        公式参考4.3.1节
        """
        densities = np.linspace(0, 150, 100)  # 密度范围
        flows = []
        speeds = []

        for density in densities:
            if density == 0:
                flows.append(0)
                speeds.append(120)  # 自由流速度
                continue

            # 计算平衡态速度
            equilibrium_speed = self._calculate_equilibrium_speed(
                density, smart_vehicle_ratio, max_platoon_size)

            # 计算流量
            flow = density * equilibrium_speed / 3.6  # 转换为veh/h
            flows.append(flow)
            speeds.append(equilibrium_speed)

        return densities, flows, speeds

    def _calculate_equilibrium_speed(self, density, p, n):
        """
        计算平衡态速度
        p: 智能车混入率
        n: 最大车队规模
        """
        if p == 1:  # 全智能车情况
            avg_headway = (1 / n) * self.parameters['acc_headway'] + \
                          ((n - 1) / n) * self.parameters['cacc_headway']
        else:  # 混合交通流
            human_ratio = 1 - p
            acc_ratio = p * (1 - p)  # ACC车辆比例
            cacc_ratio = p * p  # CACC车辆比例

            avg_headway = (human_ratio * self.parameters['human_driver_headway'] +
                           acc_ratio * self.parameters['acc_headway'] +
                           cacc_ratio * self.parameters['cacc_headway'])

        # 计算平均间距
        avg_spacing = 1 / density

        # 计算平衡态速度（简化模型）
        if avg_spacing > avg_headway * 30 + self.parameters['vehicle_length']:  # 自由流
            speed = 120
        else:  # 拥挤流
            speed = max(0, (avg_spacing - self.parameters['vehicle_length'] -
                            self.parameters['min_spacing']) / avg_headway * 3.6)

        return min(speed, 120)


class TrafficEmissionAnalyzer:
    """交通流碳排放分析器"""

    def analyze_smart_vehicle_impact(self, mixing_ratios, traffic_data):
        """
        分析智能车混入率对碳排放的影响
        基于4.4.1节
        """
        emissions_by_ratio = {}

        for ratio in mixing_ratios:
            # 更新交通流组成
            updated_traffic = self._adjust_traffic_composition(traffic_data, ratio)

            # 计算碳排放
            total_emission = self._calculate_scenario_emission(updated_traffic)
            lane_emissions = self._calculate_lane_emissions(updated_traffic)

            emissions_by_ratio[ratio] = {
                'total': total_emission,
                'by_lane': lane_emissions
            }

        return emissions_by_ratio

    def analyze_ramp_vehicle_impact(self, ramp_ratios, base_traffic):
        """
        分析下匝道车辆占比对碳排放的影响
        基于4.4.3节
        """
        emission_results = {}

        for ramp_ratio in ramp_ratios:
            # 调整下匝道车辆比例
            adjusted_traffic = self._adjust_ramp_vehicle_ratio(base_traffic, ramp_ratio)

            # 分段计算碳排放
            segment_emissions = self._calculate_segment_emissions(adjusted_traffic)
            total_emission = sum(segment_emissions.values())

            emission_results[ramp_ratio] = {
                'total': total_emission,
                'segments': segment_emissions
            }

        return emission_results





"__________________________________________________________________________"


class CruiseSystemDegradationModel:
    """巡航系统退化机理分析模型"""

    def __init__(self):
        self.degradation_scenarios = {
            'human_vehicle_ahead': self._human_vehicle_ahead_degradation,
            'max_platoon_ahead': self._max_platoon_ahead_degradation
        }

    def calculate_vehicle_proportions(self, total_vehicles, smart_ratio, max_platoon_size):
        """
        计算考虑巡航系统退化的车辆比例
        公式5.1-5.6
        """
        if smart_ratio == 1:
            # 全智能车情况
            acc_ratio = 1 / max_platoon_size
            cacc_ratio = (max_platoon_size - 1) / max_platoon_size
        else:
            # 智能车前方为人工驾驶车辆导致的退化
            acc1_ratio = smart_ratio * (1 - smart_ratio)

            # 智能车前方为达到最大规模车队导致的退化
            acc2_ratio = self._calculate_max_platoon_degradation(smart_ratio, max_platoon_size)

            # 总ACC车辆比例
            acc_ratio = acc1_ratio + acc2_ratio
            cacc_ratio = smart_ratio - acc_ratio

        human_ratio = 1 - smart_ratio

        return {
            'human_vehicles': human_ratio,
            'acc_vehicles': acc_ratio,
            'cacc_vehicles': cacc_ratio
        }

    def _calculate_max_platoon_degradation(self, p, n):
        """
        计算前方最大规模车队导致的退化比例
        公式5.3-5.5
        """
        if p == 1:
            return 1 / n

        # 计算前方有i个最大规模车队的退化情况
        total_acc_ratio = 0
        for i in range(1, 10):  # 假设最多前方有10个车队
            acc_ratio_i = (p ** i * (1 - p ** (n * i))) / (1 - p ** n)
            total_acc_ratio += acc_ratio_i

        return min(total_acc_ratio, p)  # 不能超过智能车总比例


class PlatooningTrafficModel:
    """车辆队列行驶交通流模型"""

    def calculate_platooning_fundamental_diagram(self, smart_ratio, platoon_size):
        """
        计算车辆队列行驶的基本图
        公式5.7-5
        """