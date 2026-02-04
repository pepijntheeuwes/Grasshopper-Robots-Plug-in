using static Robots.Util;

namespace Robots;

public abstract class Target : IToolpath
{
    public static Target Default { get; } = new JointTarget([0, 1.570796, 0, 0, 0, 0]);

    public Tool Tool { get; set; }
    public Frame Frame { get; set; }
    public Speed? Speed { get; set; } // 1. Change to nullable Speed?
    public Zone Zone { get; set; }
    public Command Command { get; set; }
    public double[] External { get; set; }
    public string[]? ExternalCustom { get; set; }
    public ServoParameters? ServoParameters { get; set; }
    public IEnumerable<Target> Targets => Enumerable.Repeat(this, 1);

    // 2. Modified Constructor with logic body
    protected Target(Tool? tool, Speed? speed, Zone? zone, Command? command, Frame? frame, IEnumerable<double>? external, ServoParameters? servoParameters = null)
    {
        this.Tool = tool ?? Tool.Default;
        this.Frame = frame ?? Frame.Default;
        this.Zone = zone ?? Zone.Default;
        this.Command = command ?? Command.Default;
        this.External = (external is not null) ? external.ToArray() : [];
        this.ServoParameters = servoParameters;

        // 3. Conditional Speed Assignment
        // If we have servo parameters and speed is null, leave it null.
        // Otherwise, if speed is null, fallback to Default.
        if (servoParameters != null)
        {
            this.Speed = speed;
        }
        else
        {
            this.Speed = speed ?? Speed.Default;
        }
    }

    public void AppendCommand(Command command)
    {
        var current = Command;

        if (current is null || current == Command.Default)
        {
            Command = command;
        }
        else
        {
            var group = new Commands.Group();

            if (current is Commands.Group currentGroup)
                group.AddRange(currentGroup);
            else
                group.Add(current);

            group.Add(command);
            Command = group;
        }
    }

    public Target ShallowClone() => (Target)MemberwiseClone();
    IToolpath IToolpath.ShallowClone(List<Target>? targets) => (IToolpath)MemberwiseClone();
}
