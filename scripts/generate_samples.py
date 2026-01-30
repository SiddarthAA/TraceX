"""
Generate sample requirement files for testing.
"""
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_sample_files():
    """Generate sample CSV files for HLRs and LLRs."""
    
    # Sample HLRs
    hlrs_data = {
        'id': [
            'HLR-001', 'HLR-002', 'HLR-003', 'HLR-004', 'HLR-005'
        ],
        'title': [
            'Pitch Stability Control',
            'Emergency Response System',
            'Sensor Data Processing',
            'Redundancy Management',
            'Flight Mode Transitions'
        ],
        'description': [
            'The flight control system shall maintain pitch stability within certified limits during all normal operating conditions.',
            'The system shall detect and respond to emergency conditions within 100ms with appropriate failsafe actions.',
            'The system shall process sensor data from multiple sources and provide accurate attitude information.',
            'The system shall manage redundant components and automatically switch to backup systems upon primary failure.',
            'The system shall manage transitions between different flight modes without loss of control authority.'
        ],
        'type': [
            'functional', 'safety', 'functional', 'safety', 'functional'
        ],
        'safety_level': [
            'DAL-B', 'DAL-A', 'DAL-B', 'DAL-A', 'DAL-B'
        ]
    }
    
    # Sample LLRs
    llrs_data = {
        'id': [
            'LLR-001', 'LLR-002', 'LLR-003', 'LLR-004', 'LLR-005',
            'LLR-006', 'LLR-007', 'LLR-008', 'LLR-009', 'LLR-010'
        ],
        'title': [
            'Elevator Actuator Response Time',
            'Control Law Update Rate',
            'IMU Pitch Rate Measurement',
            'Flight Data Logging',
            'Emergency Detection Algorithm',
            'Attitude Angle Calculation',
            'Redundancy Monitor',
            'Failsafe Command Generation',
            'Mode Transition Logic',
            'Control Surface Position Sensor'
        ],
        'description': [
            'The elevator actuator shall respond to control commands within 30 ms.',
            'The pitch control law shall execute at a minimum rate of 100 Hz.',
            'The IMU shall provide pitch rate measurements with latency not exceeding 10ms.',
            'The system shall log all critical flight data to non-volatile memory every 100ms.',
            'The emergency detection algorithm shall analyze sensor data every 10ms and flag anomalies.',
            'The navigation software shall calculate pitch, roll, and yaw angles from IMU data with ±0.1 degree accuracy.',
            'The redundancy monitor shall check health status of all redundant channels every 50ms.',
            'The failsafe logic shall generate safe control commands within 20ms of fault detection.',
            'The mode transition controller shall complete mode changes within 200ms.',
            'Control surface position sensors shall report positions with 1ms update rate.'
        ],
        'type': [
            'performance', 'performance', 'performance', 'diagnostic', 'safety',
            'functional', 'safety', 'safety', 'functional', 'interface'
        ],
        'component': [
            'Actuator', 'Control Software', 'IMU', 'Data Logger', 'Safety Monitor',
            'Navigation Software', 'Health Monitor', 'Safety Monitor', 'Mode Controller', 'Sensor Interface'
        ],
        'safety_level': [
            'DAL-B', 'DAL-B', 'DAL-B', 'DAL-D', 'DAL-A',
            'DAL-B', 'DAL-A', 'DAL-A', 'DAL-B', 'DAL-C'
        ]
    }
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "data" / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as CSV
    hlrs_df = pd.DataFrame(hlrs_data)
    llrs_df = pd.DataFrame(llrs_data)
    
    hlrs_df.to_csv(output_dir / "sample_hlrs.csv", index=False)
    llrs_df.to_csv(output_dir / "sample_llrs.csv", index=False)
    
    # Save as Excel
    with pd.ExcelWriter(output_dir / "sample_requirements.xlsx", engine='openpyxl') as writer:
        hlrs_df.to_excel(writer, sheet_name='HLRs', index=False)
        llrs_df.to_excel(writer, sheet_name='LLRs', index=False)
    
    print(f"✅ Sample files generated in {output_dir}/")
    print(f"   - sample_hlrs.csv ({len(hlrs_df)} HLRs)")
    print(f"   - sample_llrs.csv ({len(llrs_df)} LLRs)")
    print(f"   - sample_requirements.xlsx")


if __name__ == "__main__":
    generate_sample_files()
