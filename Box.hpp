#ifndef BOX_HPP
#define BOX_HPP

#include <boost/array.hpp>
#include <utility>
#include <algorithm>
#include "utils/array_helper.hpp"
#include "Shape.hpp"

template<typename T_>
class Box
{
public:
    typedef T_ value_type;
    typedef Vector3<T_> position_type;
    typedef T_ length_type;

public:
    Box(position_type const& position = position_type())
        : position_(position),
          vx_(create_vector<position_type>(1., 0., 0.)),
          vy_(create_vector<position_type>(0., 1., 0.)),
          vz_(create_vector<position_type>(0., 0., 1.)),
          extent_(array_gen<length_type>(1., 1., 1.)) {}

    template<typename Tarray_>
    Box(position_type const& position,
        Tarray_ const& extent = array_gen<length_type>(1., 1., 1.))
        : position_(position),
          vx_(create_vector<position_type>(1., 0., 0.)),
          vy_(create_vector<position_type>(0., 1., 0.)),
          vz_(create_vector<position_type>(0., 0., 1.))
    {
        std::copy(boost::begin(extent), boost::end(extent),
                  boost::begin(extent_));
    }

    template<typename Tarray_>
    Box(position_type const& position,
        position_type const& vx,
        position_type const& vy,
        position_type const& vz,
        Tarray_ const& extent = array_gen<length_type>(1., 1., 1.))
        : position_(position), vx_(vx), vy_(vy), vz_(vz)
    {
        std::copy(boost::begin(extent), boost::end(extent),
                  boost::begin(extent_));
    }

    Box(position_type const& position,
        position_type const& vx,
        position_type const& vy,
        position_type const& vz,
        length_type const& lx,
        length_type const& ly,
        length_type const& lz)
        : position_(position), vx_(vx), vy_(vy), vz_(vz),
          extent_(array_gen<length_type>(lx, ly, lz)) {}

    position_type const& position() const
    {
        return position_;
    }

    position_type& position()
    {
        return position_;
    }

    position_type const& unit_x() const
    {
        return vx_;
    }

    position_type& unit_x()
    {
        return vx_;
    }

    position_type const& unit_y() const
    {
        return vy_;
    }

    position_type& unit_y()
    {
        return vy_;
    }

    position_type const& unit_z() const
    {
        return vz_;
    }

    position_type& unit_z()
    {
        return vz_;
    }

    length_type const& Lx() const
    { 
        return extent_[0];
    }

    length_type& Lx()
    {
        return extent_[0];
    }

    length_type const& Ly() const
    {
        return extent_[1];
    }

    length_type& Ly()
    {
        return extent_[1];
    }

    length_type const& Lz() const
    {
        return extent_[2];
    }

    length_type& Lz()
    {
        return extent_[2];
    }

    boost::array<length_type, 3> const& extent() const
    {
        return extent_;
    }

    boost::array<length_type, 3>& extent()
    {
        return extent_;
    }

protected:
    position_type position_;
    position_type vx_, vy_, vz_;
    boost::array<length_type, 3> extent_;
};

template<typename T_>
inline boost::array<typename Box<T_>::length_type, 3>
to_internal(Box<T_> const& obj, typename Box<T_>::position_type const& pos)
{
    typedef typename Box<T_>::position_type position_type;
    position_type pos_vector(subtract(pos, obj.position()));

    return array_gen<typename Box<T_>::length_type>(
        dot_product(pos_vector, obj.unit_x()),
        dot_product(pos_vector, obj.unit_y()),
        dot_product(pos_vector, obj.unit_z()));
}

template<typename T_>
inline std::pair<typename Box<T_>::position_type,
                 typename Box<T_>::length_type>
projected_point(Box<T_> const& obj, typename Box<T_>::position_type const& pos)
{
    boost::array<typename Box<T_>::length_type, 3> x_y_z(to_internal(obj, pos));
    return std::make_pair(
        add(
            add(obj.position(), multiply(obj.unit_x(), x_y_z[0])),
            multiply(obj.unit_y(), x_y_z[1])),
        x_y_z[2]);
}

template<typename T_>
inline typename Box<T_>::length_type
distance(Box<T_> const& obj, typename Box<T_>::position_type const& pos)
{
    typedef typename Box<T_>::length_type length_type;
    boost::array<length_type, 3> x_y_z(to_internal(obj, pos));
    boost::array<length_type, 3> dx_dy_dz(subtract(abs(x_y_z), obj.extent()));

    if (dx_dy_dz[0] > 0)
    {
        if (dx_dy_dz[1] > 0)
        {
            if (dx_dy_dz[2] > 0)
            {
                return length(dx_dy_dz);
            }
            else
            {
                return length(array_slice<0, 2>(dx_dy_dz));
            }
        }
        else
        {
            if (dx_dy_dz[2] > 0)
            {
                return std::sqrt(gsl_pow_2(dx_dy_dz[0]) + gsl_pow_2(dx_dy_dz[2]));
            }
            else
            {
                return dx_dy_dz[0];
            }
        }
    }
    else
    {
        if (dx_dy_dz[1] > 0)
        {
            if (dx_dy_dz[2] > 0)
            {
                return length(array_slice<1, 3>(dx_dy_dz));
            }
            else
            {
                return dx_dy_dz[1];
            }
        }
        else
        {
            if (dx_dy_dz[2] > 0)
            {
                return dx_dy_dz[2];
            }
            else
            {
                return std::max(std::max(dx_dy_dz[0], dx_dy_dz[1]), dx_dy_dz[2]);
            }
        }
    }
}

template<typename T_>
struct is_shape<Box<T_> >: public boost::mpl::true_ {};

template<typename T_>
struct shape_position_type<Box<T_> > {
    typedef typename Box<T_>::position_type type;
};

template<typename Tstrm_, typename Ttraits_, typename T_>
inline std::basic_ostream<Tstrm_, Ttraits_>& operator<<(std::basic_ostream<Tstrm_, Ttraits_>& strm,
        const Box<T_>& v)
{
    strm << "{" << v.position() <<  ", " << v.unit_x() << ", " << v.unit_y() << ", " << v.unit_z() << "," << v.Lx() << ", " << v.Ly() << ", " << v.Lz() << "}";
    return strm;
}


#if defined(HAVE_TR1_FUNCTIONAL)
namespace std { namespace tr1 {
#elif defined(HAVE_STD_HASH)
namespace std {
#elif defined(HAVE_BOOST_FUNCTIONAL_HASH_HPP)
namespace boost {
#endif

template<typename T_>
struct hash<Box<T_> >
{
    typedef Box<T_> argument_type;

    std::size_t operator()(argument_type const& val)
    {
        return hash<typename argument_type::position_type>()(val.position()) ^
            hash<typename argument_type::position_type>()(val.unit_x()) ^
            hash<typename argument_type::position_type>()(val.unit_y()) ^
            hash<typename argument_type::position_type>()(val.unit_z()) ^
            hash<typename argument_type::length_type>()(val.extent()[0]) ^
            hash<typename argument_type::length_type>()(val.extent()[1]) ^
            hash<typename argument_type::length_type>()(val.extent()[2]);
    }
};

#if defined(HAVE_TR1_FUNCTIONAL)
} } // namespace std::tr1
#elif defined(HAVE_STD_HASH)
} // namespace std
#elif defined(HAVE_BOOST_FUNCTIONAL_HASH_HPP)
} // namespace boost
#endif

#endif /* BOX_HPP */
