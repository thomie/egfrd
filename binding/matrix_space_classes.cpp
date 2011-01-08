#include "binding_common_EGFRDSimulator.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "../MatrixSpace.hpp"
#include "MatrixSpace.hpp"

namespace binding {
typedef EGFRDSimulatorTraits::shell_id_type ShellID;
typedef EGFRDSimulator::spherical_shell_type SphericalShell;
typedef EGFRDSimulator::cylindrical_shell_type CylindricalShell;
typedef ::MatrixSpace<SphericalShell, ShellID> SphericalShellContainer;
typedef ::MatrixSpace<CylindricalShell, ShellID> CylindricalShellContainer;

void register_spherical_shell_container_class()
{
    register_matrix_space_class<SphericalShellContainer>(
            "SphericalShellContainer");
}

void register_cylindrical_shell_container_class()
{
    register_matrix_space_class<CylindricalShellContainer>(
            "CylindricalShellContainer");
}

} // namespace binding
