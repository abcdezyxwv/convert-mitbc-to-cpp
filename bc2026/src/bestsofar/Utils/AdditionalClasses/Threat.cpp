#include "Utils/AdditionalClasses/Threat.hpp"

namespace Utils {
namespace AdditionalClasses {

// The Java fields are `static` (see Threat.hpp) - one shared instance.
MapLocation Threat::loc;
Direction Threat::dir;
bool Threat::threat = false;

}  // namespace AdditionalClasses
}  // namespace Utils
