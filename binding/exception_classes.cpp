#ifdef HAVE_CONFIG_H
#include <config.h>
#endif /* HAVE_CONFIG_H */

#include <exception>
#include <stdexcept>
#include "peer/wrappers/exception/exception_wrapper.hpp"
#include "../exceptions.hpp"

namespace binding {
typedef ::not_found NotFound;
typedef ::already_exists AlreadyExists;
typedef ::illegal_state IllegalState;

void register_exception_classes()
{
    peer::wrappers::exception_wrapper<NotFound, peer::wrappers::py_exc_traits<&PyExc_LookupError> >::__register_class("NotFound");
    peer::wrappers::exception_wrapper<AlreadyExists, peer::wrappers::py_exc_traits<&PyExc_StandardError> >::__register_class("AlreadyExists");
    peer::wrappers::exception_wrapper<IllegalState, peer::wrappers::py_exc_traits<&PyExc_StandardError> >::__register_class("IllegalState");
}

} // namespace binding
