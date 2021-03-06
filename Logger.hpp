#ifndef LOGGER_HPP
#define LOGGER_HPP

#include <cstdarg>

class Logger
{
public:
    enum level
    {
        L_OFF = 0,
        L_DEBUG = 1,
        L_INFO = 2,
        L_WARNING = 3,
        L_ERROR = 4,
        L_FATAL = 5
    };

public:
    virtual ~Logger();

    void debug(char const* format, ...)
    {
        va_list ap;
        va_start(ap, format);
        logv(L_DEBUG, format, ap);
        va_end(ap);
    }

    void info(char const* format, ...)
    {
        va_list ap;
        va_start(ap, format);
        logv(L_INFO, format, ap);
        va_end(ap);
    }

    void warn(char const* format, ...)
    {
        va_list ap;
        va_start(ap, format);
        logv(L_WARNING, format, ap);
        va_end(ap);
    }

    void error(char const* format, ...)
    {
        va_list ap;
        va_start(ap, format);
        logv(L_ERROR, format, ap);
        va_end(ap);
    }

    void fatal(char const* format, ...)
    {
        va_list ap;
        va_start(ap, format);
        logv(L_FATAL, format, ap);
        va_end(ap);
    }

    void log(enum level lv, char const* format, ...)
    {
        va_list ap;
        va_start(ap, format);
        logv(lv, format, ap);
        va_end(ap);
    }

    virtual void set_name(char const* name) = 0;

    virtual void logv(enum level lv, char const* format, va_list ap) = 0;

    static Logger& get_logger(char const* name);
};

class LoggerFactory
{
public:
    virtual ~LoggerFactory();

    virtual Logger* create() const = 0;

    static LoggerFactory& get_logger_factory(char const* name);
};

#ifdef DEBUG
#   define LOG_DEBUG(args) log_.debug args
#else
#   define LOG_DEBUG(args)
#endif 

#endif /* LOGGER_HPP */
