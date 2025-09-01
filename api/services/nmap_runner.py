import subprocess
import tempfile
import logging
from ..schemas import ScanProfile, TimingTemplate

logger = logging.getLogger(__name__)

SCAN_PROFILES_COMMANDS = {
    ScanProfile.BASIC_VERSION_DETECTION: ["-sV", "-Pn"],
    ScanProfile.AGGRESSIVE_SCAN: ["-A", "-Pn"],
    ScanProfile.VULN_TCP_EVASIVE: ["-n", "-A", "-Pn", "-sT", "-sC", "--script=vuln", "-f", "--mtu", "24"],
    ScanProfile.VULN_SYN_STEALTH: ["-n", "-A", "-Pn", "-sS", "-sC", "--script=vuln", "-f", "--mtu", "24"],
    ScanProfile.PROXY_VULN_SCAN: ["proxychains", "-q", "nmap", "-A", "-Pn", "-sT", "--script=vuln"]
}

def run_nmap_scan(scan_id: str, targets: list[str], profile: str, ports: str | None, timing_template: str) -> tuple[str, str, str]:
    try:
        profile_enum = ScanProfile(profile)
    except ValueError:
        raise ValueError(f"Perfil de scan inválido '{profile}' especificado")

    if profile_enum not in SCAN_PROFILES_COMMANDS:
        raise ValueError("Perfil de scan não implementado")

    with tempfile.NamedTemporaryFile(
        delete=False, mode='w', suffix='.xml', prefix=f"nmap_{scan_id}_"
    ) as tmp_xml:
        xml_output_path = tmp_xml.name
    
    base_command = SCAN_PROFILES_COMMANDS[profile_enum]
    command = []
    
    if profile_enum == ScanProfile.PROXY_VULN_SCAN:
        command.extend(base_command)
    else:
        command.append("/usr/bin/nmap")
        command.extend(base_command)

    command.extend(["-oX", xml_output_path])
    command.append(f"-{timing_template}")
    command.append("-vv")
    
    if ports:
        command.extend(["-p", ports])
    
    command.extend(targets)

    logger.info(f"Executando Nmap para o scan {scan_id}: {' '.join(command)}")
    
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=7200,
        )
        
        stdout_path = f"{xml_output_path}.out"
        stderr_path = f"{xml_output_path}.err"

        with open(stdout_path, "w") as f_out:
            f_out.write(process.stdout)
        with open(stderr_path, "w") as f_err:
            f_err.write(process.stderr)
        
        if process.returncode != 0:
            logger.error(f"Scan Nmap {scan_id} falhou com código {process.returncode}: {process.stderr}")
            
        return xml_output_path, stdout_path, stderr_path

    except subprocess.TimeoutExpired:
        logger.error(f"Scan Nmap {scan_id} excedeu o tempo limite.")
        return "", "", ""
    except FileNotFoundError:
        logger.critical("Comando nmap ou proxychains não encontrado.")
        return "", "", ""