# Root requirement

User explicitly requires KernelSU Next integrated in the kernel. A stock kernel with empty KernelSU stubs does not satisfy this requirement.

KernelSU Next repository: https://github.com/KernelSU-Next/KernelSU-Next
Pinned dev commit: b427a3f9c2421a443f961007bfce66b25486643f

Both configuration and compilation workflows fetch the pinned source, link its kernel directory into drivers/kernelsu, enable CONFIG_KSU, and verify the resolved config. SUSFS and KPM are not requested by this root clarification and remain disabled for this initial build. Compilation and runtime root are not yet verified.
