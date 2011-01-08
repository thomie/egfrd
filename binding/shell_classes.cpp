#include "binding_common_EGFRDSimulator.hpp"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include "Shell.hpp"

namespace binding {
typedef EGFRDSimulator::spherical_shell_type SphericalShell;
typedef EGFRDSimulator::cylindrical_shell_type CylindricalShell;

void register_spherical_shell_class()
{
    ShellWrapper<SphericalShell>::__register_class("SphericalShell");
}

void register_cylindrical_shell_class()
{
    ShellWrapper<CylindricalShell>::__register_class("CylindricalShell");
}

} // namespace binding
