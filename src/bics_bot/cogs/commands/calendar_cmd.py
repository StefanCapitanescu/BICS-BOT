import nextcord
from nextcord.ext import commands
from nextcord import application_command, Interaction

from bics_bot.utils.channels_utils import (
    retrieve_courses_text_channels_names,
    get_user_year,
)
from bics_bot.embeds.logger_embed import LoggerEmbed
from bics_bot.dropdowns.calendar_dropdown import CalendarView
from bics_bot.utils.calendar import Calendar


class CalendarCmd(commands.Cog):
    """This class represents the commands to interact with the calendar system.

    </calendar_add> will let students enter a HW or an exam into the calendar
        system with various details about the assignment/exam for their year.

    </calendar_delete> will let students remove multiple entries from the
        calendar from their year.

    Attributes:
        client: Required by the API, not directly utilized.
    """

    def __init__(self, client):
        self.client = client

    @application_command.slash_command(
        description="Allow students to enter a HW/exam into the calendar with info such as deadline.",
    )
    async def calendar_add(
        self,
        interaction: Interaction,
        type: str = nextcord.SlashOption(
            description="The type of event.",
            required=True,
            choices=[
                "Homework",
                "Midterm",
                "Quiz",
                "Final",
            ],
        ),
        course: str = nextcord.SlashOption(
            description="For example; Linear Algebra 1", required=True
        ),
        graded: bool = nextcord.SlashOption(
            description="Is this event graded?",
            required=True,
            choices={True, False},
        ),
        deadline_date: str = nextcord.SlashOption(
            description="Date format: <DAY.MONTH.YEAR>. Example (June 5th, 2023): 05.06.2023",
            required=True,
        ),
        deadline_time: str = nextcord.SlashOption(
            description="Time format: <HOUR:MINUTE>. Use 24-hour clock. Examples: 09:30, 15:45, 00:00, 23:59",
            required=True,
        ),
        location: str = nextcord.SlashOption(
            description="Room of the event. For example: MSA 3.050",
            required=False,
            default="",
        ),
    ) -> None:
        year = get_user_year(interaction.user)
        calendar = Calendar()
        calendar.add_entry(
            type, course, graded, deadline_date, deadline_time, location, year
        )
        calendar.export_calendar()
        await calendar.update_caledar_text_channel(interaction)

        await interaction.response.send_message(
            embed=LoggerEmbed(
                f"Data added to calendar.\n\nType: {type}\nCourse: {course}\nGraded: {graded}\nDeadline Date: {deadline_date}\nDeadline Time: {deadline_time}\nLocation: {location}",
            ),
            ephemeral=True,
        )

    @application_command.slash_command(
        description="Allow students to remove a HW/exam from the calendar.",
    )
    async def calendar_delete(self, interaction: Interaction) -> None:
        calendar = Calendar()

        view = CalendarView(interaction.user, interaction.guild, calendar)
        await interaction.response.send_message(
            view=view,
            ephemeral=True,
        )

    @application_command.slash_command(
        description="Allow students to view their own calendar.",
    )
    async def calendar_view(self, interaction: Interaction) -> None:
        enrolled_courses = self.get_courses_enrolled(
            interaction.user,
            interaction.guild,
        )
        calendar = Calendar()
        msg = ""
        for entry in calendar.retrieve_entries():
            if entry.course in enrolled_courses:
                msg += f"{entry}\n"
        if msg == "":
            await interaction.response.send_message(
                content="No deadlines for you. Enjoy your free time :)",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(content=msg, ephemeral=True)

    def get_courses_enrolled(
        self, user: Interaction.user, guild: Interaction.guild
    ) -> dict[str, bool]:
        """Retrieves the courses a student is enrolled to.

        Technically, it returns the courses that the student can view it by
        any means necessary (member level permission, role level permission,
        admin rights).

        Args:
            user: the user who is doing the </enroll> or <unenroll> request.
            guild: the server object, containing information on text channels
              necessary for this opeation

        Returns:
            dictionary where the keys are the courses the student can see
        """
        enrolled: dict[str, bool] = {}
        channels = guild.text_channels
        courses_channels_names = retrieve_courses_text_channels_names(guild)

        for channel in channels:
            if (
                channel.name in courses_channels_names
                and user in channel.members
            ):
                enrolled[channel.topic] = True

        # print(enrolled)
        return enrolled


def setup(client):
    """Function used to setup nextcord cogs"""
    client.add_cog(CalendarCmd(client))
