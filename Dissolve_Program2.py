import subprocess
import time

def get_user_inputs():
    print("=== Surface Evolver Configuration ===\n")

    evolver_path = input("Enter the path to evolver.exe. Remove Quotes: ").strip()
    fe_file = input("Enter the path to your .fe file. Remove Quotes: ").strip()

    steps = input("Enter number of steps [default: 5]: ").strip()
    steps = int(steps) if steps else 5

    step_delay = input("Enter step delay in seconds [default: 2]: ").strip()
    step_delay = float(step_delay) if step_delay else 2.0

    evolve_amount = input("Enter how many evolution iterations per step [default: 1]: ").strip()
    evolve_amount = int(evolve_amount) if evolve_amount else 1

    filename_prefix = input("Enter a prefix for saved snapshots [default: dissolve]: ").strip()
    filename_prefix = filename_prefix if filename_prefix else "dissolve"

    print("Enter extra commands one per line (e.g. 's' press enter, 'q' press enter).")
    print("Type 'done' when finished, or just press Enter to skip.")
    extra_commands = []
    while True:
        cmd = input("  Command: ").strip()
        if cmd.lower() == "done" or cmd == "":
            break
        extra_commands.append(cmd)

    return evolver_path, fe_file, steps, step_delay, evolve_amount, filename_prefix, extra_commands


def run_evolver_dissolve(
    evolver_path,
    fe_file,
    steps=5,
    step_delay=2,
    startup_delay=2,
    filename_prefix="dissolve",
    evolve_amount=1,
    extra_commands=None
):
    proc = subprocess.Popen(
        [evolver_path, fe_file],
        stdin=subprocess.PIPE,
        text=True
    )

    time.sleep(startup_delay)

    if extra_commands:
        for cmd in extra_commands:
            proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    for i in range(steps):
        print(f"Step {i+1}/{steps}: dissolving a non-fixed edge, then evolving {evolve_amount} iterations")
        proc.stdin.write(
            "foreach edge ee where (valence == 2) and (not ee.fixed) and (random < 0.05) do { dissolve ee; break; }\n"
        )
        proc.stdin.write(f"g{evolve_amount}\n")  

        filename = f"{filename_prefix}_{i+1}.ps"
        proc.stdin.write(f'postscript "{filename}"\n')

        proc.stdin.flush()
        time.sleep(step_delay)

    input("Press Enter to quit Evolver...")

    proc.stdin.write("q\n")
    proc.stdin.flush()


if __name__ == "__main__":
    evolver_path, fe_file, steps, step_delay, evolve_amount, filename_prefix, extra_commands = get_user_inputs()

    run_evolver_dissolve(
        evolver_path=evolver_path,
        fe_file=fe_file,
        steps=steps,
        step_delay=step_delay,
        evolve_amount=evolve_amount,
        filename_prefix=filename_prefix,
        extra_commands=extra_commands if extra_commands else None
    )