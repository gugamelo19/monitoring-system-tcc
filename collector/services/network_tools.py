import shutil
import subprocess


class ExternalToolUnavailable(RuntimeError):
    pass


class NetworkToolRunner:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    @staticmethod
    def _require_tool(tool_name: str) -> str:
        executable = shutil.which(tool_name)
        if executable is None:
            raise ExternalToolUnavailable(f"{tool_name} não encontrado no PATH.")
        return executable

    def _run(self, command: list[str]) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"Comando excedeu o limite de {self.timeout} segundos."
            ) from exc
        except OSError as exc:
            raise ExternalToolUnavailable(
                f"Nao foi possivel executar {command[0]}."
            ) from exc

    def run_nmap_port_scan(
        self,
        target_ip: str,
        ports: list[int],
        scan_type: str = "-sS",
    ) -> subprocess.CompletedProcess:
        nmap = self._require_tool("nmap")
        port_argument = ",".join(str(port) for port in ports)
        command = [
            nmap,
            scan_type,
            "-Pn",
            "--max-retries",
            "1",
            "-p",
            port_argument,
            target_ip,
        ]

        result = self._run(command)

        if result.returncode != 0 and scan_type == "-sS":
            fallback_command = command.copy()
            fallback_command[1] = "-sT"
            result = self._run(fallback_command)

        return result

    def run_hping3_icmp_flood(
        self,
        target_ip: str,
        count: int,
    ) -> subprocess.CompletedProcess:
        hping3 = self._require_tool("hping3")
        command = [
            hping3,
            "--icmp",
            "--fast",
            "-c",
            str(count),
            target_ip,
        ]
        return self._run(command)
