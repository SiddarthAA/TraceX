"""
Requirements loader - ingests HLRs and LLRs from various formats.
"""
import pandas as pd
import json
from typing import List, Tuple, Dict, Any
from pathlib import Path
from src.models import HLR, LLR


class RequirementsLoader:
    """Load requirements from CSV/Excel/JSON files."""
    
    @staticmethod
    def load_from_csv(hlr_file: str, llr_file: str) -> Tuple[List[HLR], List[LLR]]:
        """Load requirements from CSV files."""
        hlr_df = pd.read_csv(hlr_file)
        llr_df = pd.read_csv(llr_file)
        
        return RequirementsLoader._parse_dataframes(hlr_df, llr_df)
    
    @staticmethod
    def load_from_excel(file_path: str, hlr_sheet: str = "HLRs", llr_sheet: str = "LLRs") -> Tuple[List[HLR], List[LLR]]:
        """Load requirements from Excel file with separate sheets."""
        hlr_df = pd.read_excel(file_path, sheet_name=hlr_sheet)
        llr_df = pd.read_excel(file_path, sheet_name=llr_sheet)
        
        return RequirementsLoader._parse_dataframes(hlr_df, llr_df)
    
    @staticmethod
    def load_from_json(hlr_data: Dict[str, Any], llr_data: Dict[str, Any]) -> Tuple[List[HLR], List[LLR]]:
        """Load requirements from JSON data."""
        hlrs = []
        llrs = []
        
        # Parse HLRs
        hlr_list = hlr_data.get("requirements", []) if isinstance(hlr_data, dict) else hlr_data
        for item in hlr_list:
            hlr = HLR(
                id=str(item.get('id', '')),
                title=str(item.get('title', '')),
                description=str(item.get('description', '')),
                type=str(item.get('type', 'other')),
                safety_level=str(item.get('safety_level', 'not_specified')),
                component=item.get('component')
            )
            hlrs.append(hlr)
        
        # Parse LLRs
        llr_list = llr_data.get("requirements", []) if isinstance(llr_data, dict) else llr_data
        for item in llr_list:
            llr = LLR(
                id=str(item.get('id', '')),
                title=str(item.get('title', '')),
                description=str(item.get('description', '')),
                type=str(item.get('type', 'other')),
                safety_level=str(item.get('safety_level', 'not_specified')),
                component=item.get('component')
            )
            llrs.append(llr)
        
        return hlrs, llrs
    
    @staticmethod
    def _parse_dataframes(hlr_df: pd.DataFrame, llr_df: pd.DataFrame) -> Tuple[List[HLR], List[LLR]]:
        """Parse dataframes into requirement objects."""
        hlrs = []
        for _, row in hlr_df.iterrows():
            hlr = HLR(
                id=str(row.get('id', '')),
                title=str(row.get('title', '')),
                description=str(row.get('description', '')),
                type=str(row.get('type', 'other')),
                safety_level=str(row.get('safety_level', 'not_specified')),
                component=str(row.get('component', '')) if pd.notna(row.get('component')) else None
            )
            hlrs.append(hlr)
        
        llrs = []
        for _, row in llr_df.iterrows():
            llr = LLR(
                id=str(row.get('id', '')),
                title=str(row.get('title', '')),
                description=str(row.get('description', '')),
                type=str(row.get('type', 'other')),
                safety_level=str(row.get('safety_level', 'not_specified')),
                component=str(row.get('component', '')) if pd.notna(row.get('component')) else None
            )
            llrs.append(llr)
        
        return hlrs, llrs
    
    @staticmethod
    def create_sample_requirements() -> Tuple[List[HLR], List[LLR]]:
        """Create sample aerospace requirements for demonstration (DO-178C compliant)."""
        hlrs = [
            HLR(
                id="HLR-001",
                title="Pitch Stability Control",
                description="The flight control system shall maintain aircraft pitch attitude within ±2 degrees of commanded pitch during normal cruise flight conditions per DO-178C DAL-B requirements.",
                type="functional",
                safety_level="DAL-B"
            ),
            HLR(
                id="HLR-002",
                title="Emergency System Response",
                description="The flight control system shall detect critical system failures and engage backup control modes within 100 milliseconds to ensure continued safe flight per DO-178C DAL-A requirements.",
                type="safety",
                safety_level="DAL-A"
            ),
            HLR(
                id="HLR-003",
                title="Attitude Data Processing",
                description="The avionics system shall continuously process inertial measurement unit (IMU) data and provide real-time aircraft attitude information (pitch, roll, yaw) with update rate of at least 50 Hz.",
                type="functional",
                safety_level="DAL-B"
            ),
            HLR(
                id="HLR-004",
                title="Control Surface Coordination",
                description="The flight control system shall coordinate elevator, aileron, and rudder movements to maintain coordinated flight and prevent adverse yaw conditions.",
                type="functional",
                safety_level="DAL-B"
            ),
            HLR(
                id="HLR-005",
                title="Flight Envelope Protection",
                description="The system shall prevent aircraft operation outside of certified flight envelope limits including angle of attack, airspeed, and load factor boundaries.",
                type="safety",
                safety_level="DAL-A"
            ),
        ]
        
        llrs = [
            LLR(
                id="LLR-001",
                title="Elevator Actuator Response Time",
                description="The elevator control surface actuator shall respond to commanded position changes within 30 milliseconds with position accuracy of ±0.5 degrees to support pitch control requirements.",
                type="performance",
                component="Flight Control Actuator",
                safety_level="DAL-B"
            ),
            LLR(
                id="LLR-002",
                title="Pitch Control Law Update Rate",
                description="The pitch control law algorithm shall execute at a minimum rate of 100 Hz to ensure stable closed-loop control and meet DO-178C timing requirements.",
                type="performance",
                component="Flight Control Computer",
                safety_level="DAL-B"
            ),
            LLR(
                id="LLR-003",
                title="IMU Data Latency Requirement",
                description="The inertial measurement unit (IMU) shall provide pitch rate and acceleration data with total sensor-to-processor latency not exceeding 10 milliseconds.",
                type="performance",
                component="Inertial Measurement Unit",
                safety_level="DAL-B"
            ),
            LLR(
                id="LLR-004",
                title="Flight Data Recording",
                description="The flight data recorder shall log all critical flight parameters including control surface positions, sensor data, and pilot inputs to non-volatile memory per FAA requirements.",
                type="diagnostic",
                component="Flight Data Recorder",
                safety_level="DAL-D"
            ),
            LLR(
                id="LLR-005",
                title="Failure Detection Algorithm",
                description="The system health monitoring function shall analyze sensor data streams every 10 milliseconds to detect out-of-range conditions, sensor failures, or conflicting measurements.",
                type="safety",
                component="System Health Monitor",
                safety_level="DAL-A"
            ),
            LLR(
                id="LLR-006",
                title="Attitude Computation Function",
                description="The navigation software shall compute aircraft pitch, roll, and yaw angles from IMU gyroscope and accelerometer data using quaternion-based algorithms with computational accuracy better than 0.1 degrees.",
                type="functional",
                component="Flight Control Computer",
                safety_level="DAL-B"
            ),
            LLR(
                id="LLR-007",
                title="Backup Control Mode Activation",
                description="Upon detection of primary control system failure, the backup control mode shall be activated within 50 milliseconds and provide degraded but safe aircraft control capability.",
                type="safety",
                component="Backup Flight Control",
                safety_level="DAL-A"
            ),
            LLR(
                id="LLR-008",
                title="Aileron-Rudder Coordination Logic",
                description="During banking maneuvers, the control system shall automatically apply coordinated rudder input proportional to aileron deflection to maintain coordinated flight and prevent sideslip.",
                type="functional",
                component="Flight Control Computer",
                safety_level="DAL-B"
            ),
            LLR(
                id="LLR-009",
                title="Angle of Attack Limiting",
                description="The flight envelope protection system shall limit commanded pitch attitude to prevent angle of attack from exceeding 85% of critical angle of attack under all flight conditions.",
                type="safety",
                component="Envelope Protection System",
                safety_level="DAL-A"
            ),
            LLR(
                id="LLR-010",
                title="Airspeed Protection Logic",
                description="The system shall prevent airspeed from exceeding VNE (never exceed speed) or falling below stall speed by limiting control authority and providing pilot alerting.",
                type="safety",
                component="Envelope Protection System",
                safety_level="DAL-A"
            ),
        ]
        
        return hlrs, llrs
