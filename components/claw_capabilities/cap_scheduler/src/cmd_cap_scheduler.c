#include "cmd_cap_scheduler.h"

#include <stdio.h>
#include <stdlib.h>

#include "argtable3/argtable3.h"
#include "cap_scheduler.h"
#include "esp_console.h"

static struct {
    struct arg_lit *list;
    struct arg_lit *reload;
    struct arg_lit *enable;
    struct arg_lit *disable;
    struct arg_lit *pause;
    struct arg_lit *resume;
    struct arg_lit *trigger;
    struct arg_str *id;
    struct arg_end *end;
} scheduler_args;

static int scheduler_func(int argc, char **argv)
{
    char *output = NULL;
    esp_err_t err;
    int operation_count;
    int nerrors = arg_parse(argc, argv, (void **)&scheduler_args);

    if (nerrors != 0) {
        arg_print_errors(stderr, scheduler_args.end, argv[0]);
        return 1;
    }

    operation_count = scheduler_args.list->count + scheduler_args.reload->count +
                      scheduler_args.enable->count + scheduler_args.disable->count +
                      scheduler_args.pause->count + scheduler_args.resume->count +
                      scheduler_args.trigger->count;
    if (operation_count != 1) {
        printf("Exactly one operation must be specified\n");
        return 1;
    }

    if (scheduler_args.reload->count) {
        err = cap_scheduler_reload();
        if (err != ESP_OK) {
            printf("scheduler reload failed: %s\n", esp_err_to_name(err));
            return 1;
        }
        printf("scheduler definitions reloaded\n");
        return 0;
    }

    if (scheduler_args.list->count) {
        output = calloc(1, 8192);
        if (!output) {
            printf("Out of memory\n");
            return 1;
        }
        err = cap_scheduler_list_json(output, 8192);
        if (err != ESP_OK) {
            printf("scheduler list failed: %s\n", esp_err_to_name(err));
            free(output);
            return 1;
        }
        printf("%s\n", output);
        free(output);
        return 0;
    }

    if (!scheduler_args.id->count) {
        printf("'--id' is required for this operation\n");
        return 1;
    }

    if (scheduler_args.enable->count) {
        err = cap_scheduler_enable(scheduler_args.id->sval[0], true);
    } else if (scheduler_args.disable->count) {
        err = cap_scheduler_enable(scheduler_args.id->sval[0], false);
    } else if (scheduler_args.pause->count) {
        err = cap_scheduler_pause(scheduler_args.id->sval[0]);
    } else if (scheduler_args.resume->count) {
        err = cap_scheduler_resume(scheduler_args.id->sval[0]);
    } else {
        err = cap_scheduler_trigger_now(scheduler_args.id->sval[0]);
    }

    if (err != ESP_OK) {
        printf("scheduler operation failed: %s\n", esp_err_to_name(err));
        return 1;
    }

    output = calloc(1, 2048);
    if (!output) {
        printf("Out of memory\n");
        return 1;
    }
    err = cap_scheduler_get_state_json(scheduler_args.id->sval[0], output, 2048);
    if (err != ESP_OK) {
        printf("scheduler show failed: %s\n", esp_err_to_name(err));
        free(output);
        return 1;
    }
    printf("%s\n", output);
    free(output);
    return 0;
}

void register_cap_scheduler(void)
{
    scheduler_args.list = arg_lit0("l", "list", "List scheduler entries");
    scheduler_args.reload = arg_lit0(NULL, "reload", "Reload scheduler definitions from disk");
    scheduler_args.enable = arg_lit0(NULL, "enable", "Enable one scheduler entry");
    scheduler_args.disable = arg_lit0(NULL, "disable", "Disable one scheduler entry");
    scheduler_args.pause = arg_lit0(NULL, "pause", "Pause one scheduler entry");
    scheduler_args.resume = arg_lit0(NULL, "resume", "Resume one scheduler entry");
    scheduler_args.trigger = arg_lit0(NULL, "trigger", "Trigger one scheduler entry now");
    scheduler_args.id = arg_str0("i", "id", "<id>", "Scheduler id");
    scheduler_args.end = arg_end(10);

    const esp_console_cmd_t scheduler_cmd = {
        .command = "scheduler",
        .help = "Scheduler operations.\n"
                "Examples:\n"
                " scheduler --list\n"
                " scheduler --reload\n"
                " scheduler --enable --id hourly_ping\n"
                " scheduler --pause --id hourly_ping\n"
                " scheduler --trigger --id hourly_ping\n",
        .func = scheduler_func,
        .argtable = &scheduler_args,
    };

    ESP_ERROR_CHECK(esp_console_cmd_register(&scheduler_cmd));
}
