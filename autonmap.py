#!/usr/bin/env python3
import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path

# --- Configuração ---
API_URL = os.getenv("AUTONMAP_API_URL", "http://localhost/api")
TOKEN_FILE = Path.home() / ".autonmap_token"
API_TOKEN = "_eaCqGlkdxBkznMa_zlXIT5mD7kzs420aylgk3_FMS8"

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

BANNER = f"""
{Colors.CYAN}
 █████╗ ██╗   ██╗████████╗ ██████╗     ███╗   ██ ███╗   ███╗ ╔███╗  ╔████╗
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ████╗  ██║████╗ ████║██╔══██╗██╔══██╗
███████║██║   ██║   ██║   ██║   ██║    ██╔██╗ ██║██╔████╔██║███████║██████╔╝
██╔══██║██║   ██║   ██║   ██║   ██║    ██║╚██╗██║██║╚██╔╝██║██╔══██║██╔═══╝
██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║ ╚████║██║ ╚═╝ ██║██║  ██║██║
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝  ╚═══╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝
{Colors.RESET}criado por Alexsander.
"""

# --- Funções de Formatação ---
def print_formatted_nmap(data: dict):
    try:
        nmaprun = data.get("nmaprun", {})
        if "host" not in nmaprun:
            if nmaprun.get("runstats", {}).get("hosts", {}).get("@up") == "0":
                print(f"{Colors.RED}Host está offline ou não respondeu ao ping de descoberta.{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}Nenhum host encontrado no resultado do scan.{Colors.RESET}")
            return

        host = nmaprun.get("host")
        if not isinstance(host, list): host = [host]

        for h in host:
            address = h.get("address", {})
            hostnames = h.get("hostnames", {})
            hostname_str = f"({address.get('@addr', 'N/A')})"
            if hostnames and hostnames.get("hostname"):
                names = hostnames["hostname"]
                if not isinstance(names, list): names = [names]
                hostname_str = f"{names[0].get('@name', '')} {hostname_str}"

            print(f"\n{Colors.BOLD}Nmap scan report for {hostname_str}{Colors.RESET}")
            print(f"Host is up ({h.get('status', {}).get('@reason', 'N/A')}).")

            ports_data = h.get("ports", {})
            if ports_data:
                extraports = ports_data.get("extraports", {})
                if extraports: print(f"Not shown: {extraports.get('@count', 'N/A')} {extraports.get('@state', 'N/A')} ports")

                print(f"\n{Colors.GREEN}PORT      STATE   SERVICE           VERSION{Colors.RESET}")
                open_ports = ports_data.get("port", [])
                if not isinstance(open_ports, list): open_ports = [open_ports]
                for port in open_ports:
                    port_id = f"{port.get('@portid', '')}/{port.get('@protocol', '')}"
                    state = port.get("state", {}).get("@state", "")
                    service = port.get("service", {})
                    version_str = f"{service.get('@product', '')} {service.get('@version', '')} {service.get('@extrainfo', '')}".strip()
                    print(f"{port_id:<9} {state:<7} {service.get('@name', ''):<17} {version_str}")
                    scripts = port.get("script", [])
                    if not isinstance(scripts, list): scripts = [scripts]
                    for script in scripts:
                        script_output = script.get('@output', '').replace('\n', '\n| ')
                        print(f"|_ {script.get('@id', '')}: {script_output}")
            print("-" * 40)
    except Exception as e:
        print(f"Erro ao processar o resultado do scan: {e}", file=sys.stderr)
        json.dump(data, sys.stdout, indent=2)

# --- Funções de Interação com a API ---
def resolve_token(cli_token: str = None) -> str:
    if cli_token: return cli_token
    if os.getenv("AUTONMAP_API_TOKEN"): return os.getenv("AUTONMAP_API_TOKEN")
    if API_TOKEN: return API_TOKEN
    if TOKEN_FILE.exists(): return TOKEN_FILE.read_text().strip()
    
    token = input("Por favor, cole seu token de API da autonmap: ").strip()
    if token:
        TOKEN_FILE.write_text(token)
        TOKEN_FILE.chmod(0o600)
        print(f"{Colors.GREEN}Token salvo em {TOKEN_FILE} para uso futuro.{Colors.RESET}")
        return token
    
    print(f"{Colors.RED}Erro: Token da API não fornecido.{Colors.RESET}", file=sys.stderr)
    sys.exit(1)

def execute_and_wait(payload: dict, headers: dict):
    try:
        response = requests.post(f"{API_URL}/v1/scans/", headers=headers, json=payload)
        response.raise_for_status()
        scan_id = response.json()['id']
        print(f"✅ Scan enfileirado com sucesso. ID: {scan_id}")
        print("⏳ Aguardando a conclusão...")

        while True:
            status_response = requests.get(f"{API_URL}/v1/scans/{scan_id}", headers=headers)
            status_response.raise_for_status()
            current_status = status_response.json()['status']
            
            print(f"   - Status atual: {Colors.CYAN}{current_status}{Colors.RESET}         ", end='\r', flush=True)
            
            if current_status in ["succeeded", "failed"]:
                print(f"\n✅ Tarefa concluída com status: {current_status}!")
                break
            time.sleep(15)

        if current_status == "succeeded":
            print("\n" + "--- Resultado Final do Scan ---")
            result_response = requests.get(f"{API_URL}/v1/scans/{scan_id}/result.json", headers=headers)
            result_response.raise_for_status()
            print_formatted_nmap(result_response.json())
        else:
            print(f"\n{Colors.RED}❌ O scan falhou. Verifique os logs do worker para mais detalhes.{Colors.RESET}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erro de comunicação com a API: {e}", file=sys.stderr)

# --- Lógica do Modo Interativo ---
def run_interactive_mode(token: str):
    print(BANNER)
    print(f"{Colors.CYAN}Enjoy!{Colors.RESET}\n")

    headers = {"X-API-Token": token, "Content-Type": "application/json"}
    target = input("Target (IP or Domain): ")
    if not target: return
    
    menu = {
        '1': ("basic_version_detection", None), '2': ("aggressive_scan", None),
        '3': ("aggressive_scan", "1-65535"), '4': ("vuln_tcp_evasive", None),
        '5': ("vuln_tcp_evasive", None), '6': ("vuln_tcp_evasive", "1-65535"),
        '7': ("vuln_syn_stealth", None), '8': ("vuln_syn_stealth", "1-65535"),
        '9': ("proxy_vuln_scan", None), '0': ("proxy_vuln_scan", "1-65535"),
    }
    
    print("\nSelect an option:\n")
    print(f"{Colors.RED}[1]{Colors.RESET} nmap -sV")
    print(f"{Colors.RED}[2]{Colors.RESET} nmap -A")
    print(f"{Colors.RED}[3]{Colors.RESET} nmap -A -p 1-65535")
    print(f"{Colors.YELLOW}[4-6]{Colors.RESET} Vuln Scan (TCP Evasivo)")
    print(f"{Colors.YELLOW}[7-8]{Colors.RESET} Vuln Scan (SYN Furtivo)")
    print(f"{Colors.GREEN}[9-0]{Colors.RESET} Proxychains Vuln Scan{Colors.RESET}\n")

    choice = input("Enter your choice (0-9): ")
    if choice not in menu:
        print("Opção inválida.")
        return
        
    profile, ports = menu[choice]

    print("\nTiming templates:\n")
    print(f"T0 --->{Colors.CYAN} Paranoid {Colors.RESET}")
    print(f"T1 --->{Colors.CYAN} Sneaky{Colors.RESET}")
    print(f"T2 --->{Colors.GREEN} Polite{Colors.RESET}")
    print(f"T3 --->{Colors.GREEN} Normal{Colors.RESET}")
    print(f"T4 --->{Colors.YELLOW} Aggressive{Colors.RESET}")
    print(f"T5 --->{Colors.RED} Insane{Colors.RESET}")
    
    timing_input = input("Select Timing (0-5): ").strip().upper().replace('T', '')
    if timing_input not in ['0', '1', '2', '3', '4', '5']:
        print("Timing inválido. Usando T3 (Normal).")
        timing_input = '3'
    
    timing = f"T{timing_input}"
    
    payload = {"targets": [target], "profile": profile, "timing_template": timing}
    if ports: payload["ports"] = ports
        
    execute_and_wait(payload, headers)

# --- CLI Principal ---
def main():
    parser = argparse.ArgumentParser(description="Cliente CLI para a API autonmap.", add_help=False)
    parser.add_argument("-t", "--target", help="O alvo do scan.")
    parser.add_argument("-p", "--profile", choices=[
        "basic_version_detection", "aggressive_scan", "vuln_tcp_evasive", 
        "vuln_syn_stealth", "proxy_vuln_scan"
    ], help="O perfil de scan a ser utilizado.")
    parser.add_argument("-P", "--ports", help="Define as portas a serem escaneadas.")
    parser.add_argument("-T", "--timing", default="T3", choices=["T0", "T1", "T2", "T3", "T4", "T5"], help="Define o timing template.")
    parser.add_argument("-k", "--token", help="Token da API para esta execução.")
    parser.add_argument("-h", "--help", action="store_true", help="Mostra esta ajuda.")
    
    if len(sys.argv) == 1:
        token = resolve_token()
        run_interactive_mode(token)
        return

    args = parser.parse_args()
    if args.help:
        parser.print_help()
        return
    if not args.target or not args.profile:
        print("Erro: os argumentos -t (alvo) e -p (perfil) são obrigatórios no modo não-interativo.")
        parser.print_help()
        return

    token = resolve_token(args.token)
    headers = {"X-API-Token": token, "Content-Type": "application/json"}
    payload = {"targets": [args.target], "profile": args.profile, "timing_template": args.timing}
    if args.ports: payload["ports"] = args.ports
    execute_and_wait(payload, headers)

if __name__ == "__main__":
    main()
