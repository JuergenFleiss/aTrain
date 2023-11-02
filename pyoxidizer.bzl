def make_exe():
    dist = default_python_distribution()
    policy = dist.make_python_packaging_policy()
    policy.extension_module_filter = "all"
    policy.include_distribution_sources = True
    policy.include_distribution_resources = False
    policy.include_test = False

    python_config = dist.make_python_interpreter_config()
    python_config.run_command = "from aTrain import run_app; run_app()"

    exe = dist.to_python_executable(
        name="aTrain",
        packaging_policy=policy,
        config=python_config,
    )
    exe.windows_subsystem = "windows"
    exe.add_python_resources(exe.pip_install([CWD]))
    return exe

def make_embedded_resources(exe):
    return exe.to_embedded_resources()

def make_install(exe):
    files = FileManifest()
    files.add_python_resource("aTrain", exe)
    return files

def make_msi(exe):
    return exe.to_wix_msi_builder(
        "myapp",
        "My Application",
        "1.0",
        "Alice Jones"
    )

def register_code_signers():
    if not VARS.get("ENABLE_CODE_SIGNING"):
        return

register_code_signers()

register_target("exe", make_exe)
register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
register_target("install", make_install, depends=["exe"], default=True)
register_target("msi_installer", make_msi, depends=["exe"])

resolve_targets()
